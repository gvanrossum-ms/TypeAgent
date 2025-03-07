// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import {
    MessageSourceRole,
    PromptSectionProvider,
    SearchOptions,
} from "typeagent";
import {
    Conversation,
    ConversationSearchOptions,
    SearchActionResponse,
    SearchTermsActionResponse,
    SearchTermsActionResponseV2,
} from "./conversation.js";
import { createSearchResponse, SearchResponse } from "./searchResponse.js";
import {
    Filter,
    GetAnswerAction,
    ResponseStyle,
} from "./knowledgeSearchSchema.js";
import { SetOp } from "../setOperations.js";
import {
    KnowledgeActionTranslator,
    createKnowledgeActionTranslator,
} from "./knowledgeActions.js";
import {
    AnswerGenerator,
    AnswerStyle,
    createAnswerGenerator,
} from "./answerGenerator.js";
import { PromptSection } from "typechat";
import { ChatModel } from "aiclient";
import {
    GetAnswerWithTermsAction,
    SearchTermsAction,
    TermFilter,
} from "./knowledgeTermSearchSchema.js";
import {
    GetAnswerWithTermsActionV2,
    SearchTermsActionV2,
    TermFilterV2,
} from "./knowledgeTermSearchSchema2.js";
import { createTopicSearchOptions } from "./topics.js";
import { EntitySearchOptions } from "./entities.js";

export type SearchProcessorSettings = {
    contextProvider?: PromptSectionProvider | undefined;
    defaultEntitySearchOptions?: EntitySearchOptions | undefined;
};

export type SearchProcessingOptions = {
    maxMatches: number;
    minScore: number;
    maxMessages: number;
    entitySearch?: EntitySearchOptions | undefined;
    fallbackSearch?: SearchOptions | undefined;
    threadSearch?: SearchOptions | undefined;
    skipAnswerGeneration?: boolean | undefined;
    skipEntitySearch?: boolean | undefined;
    skipTopicSearch?: boolean | undefined;
    skipActionSearch?: boolean | undefined;
    skipMessages?: boolean | undefined;
    progress?: ((action: any) => void) | undefined;
};

export interface ConversationSearchProcessor {
    settings: SearchProcessorSettings;
    actions: KnowledgeActionTranslator;
    answers: AnswerGenerator;

    search(
        query: string,
        options: SearchProcessingOptions,
    ): Promise<SearchActionResponse | undefined>;
    searchTerms(
        query: string,
        filters: TermFilter[] | undefined,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponse | undefined>;
    searchTermsV2(
        query: string,
        filters: TermFilterV2[] | undefined,
        options: SearchProcessingOptions,
        history?: PromptSection[] | undefined,
    ): Promise<SearchTermsActionResponseV2 | undefined>;
    /**
     * Generate an answer using a prior search response
     * @param searchResponse
     */
    generateAnswer(
        query: string,
        actionResponse: SearchTermsActionResponse,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponse>;
    /**
     * Generate an answer to the prior search response
     * @param query
     * @param actionResponse
     * @param options
     */
    generateAnswerV2(
        query: string,
        actionResponse: SearchTermsActionResponseV2,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponseV2>;
    buildContext(
        query: string,
        options: SearchProcessingOptions,
    ): Promise<PromptSection[] | undefined>;

    searchMessages(
        query: string,
        options: SearchOptions,
        maxMessageChars?: number,
    ): Promise<SearchResponse>;
}

export function createSearchProcessor(
    conversation: Conversation,
    actionModel: ChatModel,
    answerModel: ChatModel,
    searchProcessorSettings?: SearchProcessorSettings,
): ConversationSearchProcessor {
    const settings = searchProcessorSettings ?? {};
    const searchTranslator = createKnowledgeActionTranslator(actionModel);
    const answers = createAnswerGenerator(answerModel);

    const thisProcessor: ConversationSearchProcessor = {
        settings,
        actions: searchTranslator,
        answers,
        search,
        searchTerms,
        searchTermsV2,
        buildContext,
        generateAnswer,
        generateAnswerV2,
        searchMessages,
    };
    return thisProcessor;

    async function search(
        query: string,
        options: SearchProcessingOptions,
    ): Promise<SearchActionResponse | undefined> {
        const context = await buildContext(query, options);
        const actionResult = await searchTranslator.translateSearch(
            query,
            context,
        );
        if (!actionResult.success) {
            return undefined;
        }
        let action = actionResult.data;
        if (options.progress) {
            options.progress(action);
        }
        const rr: SearchActionResponse = {
            action,
        };
        switch (rr.action.actionName) {
            case "unknown":
                break;
            case "getAnswer":
                rr.response = await handleGetAnswers(query, rr.action, options);
                break;
        }

        return rr;
    }

    async function searchTerms(
        query: string,
        filters: TermFilter[] | undefined,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponse | undefined> {
        const context = await buildContext(query, options);
        let action: SearchTermsAction | undefined;
        if (filters && filters.length > 0) {
            // Filters already provided
            action = {
                actionName: "getAnswer",
                parameters: {
                    filters,
                },
            };
        } else {
            const actionResult = await searchTranslator.translateSearchTerms(
                query,
                context,
            );
            if (!actionResult.success) {
                return undefined;
            }
            action = actionResult.data;
        }

        if (options.progress) {
            options.progress(action);
        }
        const rr: SearchTermsActionResponse = {
            action,
        };
        if (rr.action.actionName !== "unknown") {
            rr.response = await handleGetAnswersTerms(
                query,
                rr.action,
                options,
            );
        }
        return rr;
    }

    async function searchTermsV2(
        query: string | string,
        filters: TermFilterV2[] | undefined,
        options: SearchProcessingOptions,
        history?: PromptSection[] | undefined,
    ): Promise<SearchTermsActionResponseV2 | undefined> {
        const context = await buildContext(query, options, history);
        let action: SearchTermsActionV2 | undefined;
        if (filters && filters.length > 0) {
            // Filters already provided
            action = {
                actionName: "getAnswer",
                parameters: {
                    question: query,
                    filters,
                },
            };
        } else {
            const actionResult = await searchTranslator.translateSearchTermsV2(
                query,
                context,
            );
            if (!actionResult.success) {
                return undefined;
            }
            action = actionResult.data;
        }

        if (options.progress) {
            options.progress(action);
        }
        const rr: SearchTermsActionResponseV2 = {
            action,
        };
        if (rr.action.actionName !== "unknown") {
            rr.response = await handleGetAnswersTermsV2(
                query,
                rr.action,
                options,
            );
        }
        return rr;
    }

    async function searchMessages(
        query: string,
        options: SearchOptions,
        maxMessageChars?: number,
    ): Promise<SearchResponse> {
        const response = createSearchResponse();
        //await fallbackSearch(query, undefined, response, options);
        const messageIndex = await conversation.getMessageIndex();
        if (messageIndex) {
            const matches = await messageIndex.nearestNeighbors(
                query,
                options.maxMatches,
                options.minScore,
            );
            if (matches.length > 0) {
                response.messageIds = matches.map((m) => m.item);
                response.messages = await conversation.loadMessages(
                    response.messageIds,
                );
                if (maxMessageChars && maxMessageChars > 0) {
                    let charCount = 0;
                    let i = 0;
                    for (; i < response.messages.length; ++i) {
                        const messageLength =
                            response.messages[i].value.value.length;
                        if (charCount + messageLength > maxMessageChars) {
                            break;
                        }
                        charCount += messageLength;
                    }
                    if (i > 0 && i < response.messages.length) {
                        response.messageIds.splice(i);
                        response.messages.splice(i);
                    }
                }
                response.answer = await answers.generateAnswer(
                    query,
                    undefined,
                    response,
                    true,
                    false,
                );
            }
        }

        return response;
    }

    async function buildContext(
        query: string,
        options: SearchProcessingOptions,
        history?: PromptSection[] | undefined,
    ): Promise<PromptSection[] | undefined> {
        let context: PromptSection[] | undefined;
        const timeRange = await conversation.messages.getTimeRange();
        if (timeRange) {
            context ??= [];
            context.push({
                role: MessageSourceRole.system,
                content: `ONLY IF user request explicitly asks for time ranges, THEN use the CONVERSATION TIME RANGE: "${timeRange.startDate} to ${timeRange.stopDate}"`,
            });
        }
        if (settings.contextProvider) {
            context ??= [];
            context.push(
                ...(await settings.contextProvider.getSections(query)),
            );
        }
        if (history && history.length > 0) {
            context ??= [];
            context.push(...history);
        }
        return context;
    }

    async function handleGetAnswers(
        query: string,
        action: GetAnswerAction,
        options: SearchProcessingOptions,
    ): Promise<SearchResponse> {
        const responseType = action.parameters.responseType;
        const topLevelTopicSummary = isTopicSummaryRequest(action);
        const topicLevel = topLevelTopicSummary ? 2 : 1;
        const searchOptions: ConversationSearchOptions = {
            entity: {
                maxMatches: options.maxMatches,
                minScore: options.minScore,
                combinationSetOp: SetOp.IntersectUnion,
                loadEntities: true,
            },
            topic: {
                maxMatches: topLevelTopicSummary
                    ? Number.MAX_SAFE_INTEGER
                    : options.maxMatches,
                minScore: options.minScore,
                loadTopics:
                    responseType === "Answer" || responseType === "Topics",
            },
            topicLevel,
            loadMessages: responseType === "Answer" || hasActionFilter(action),
        };
        searchOptions.action = {
            maxMatches: options.maxMatches,
            minScore: options.minScore,
            verbSearchOptions: {
                maxMatches: 1,
                minScore: options.minScore,
            },
            loadActions: false,
        };

        adjustRequest(query, action, searchOptions);

        const response = await conversation.search(
            action.parameters.filters,
            searchOptions,
        );
        await adjustResponse(query, action, response, searchOptions, options);
        response.answer = await answers.generateAnswer(
            query,
            action.parameters.responseStyle,
            response,
            false,
        );
        if (response.answer?.type === "NoAnswer" && options.fallbackSearch) {
            await fallbackSearch(
                query,
                action.parameters.responseStyle,
                response,
                options.fallbackSearch,
            );
        }
        return response;
    }

    async function handleGetAnswersTerms(
        query: string,
        action: GetAnswerWithTermsAction,
        options: SearchProcessingOptions,
    ): Promise<SearchResponse> {
        const topLevelTopicSummary = isSummaryRequest(action);
        const searchOptions = createSearchOptions(
            topLevelTopicSummary,
            options,
        );
        const response = await conversation.searchTerms(
            action.parameters.filters,
            searchOptions,
        );
        await adjustMessages(query, response, searchOptions, options);
        response.topKSettings = answers.settings.topK;
        if (!options.skipAnswerGeneration) {
            await generateAnswerForSearchTerms(
                query,
                response,
                options,
                //action.parameters.answerType,
            );
        }
        return response;
    }

    async function handleGetAnswersTermsV2(
        query: string,
        action: GetAnswerWithTermsActionV2,
        options: SearchProcessingOptions,
    ): Promise<SearchResponse> {
        query = action.parameters.question;
        const topLevelTopicSummary = isSummaryRequestV2(action);
        const searchOptions = createSearchOptions(
            topLevelTopicSummary,
            options,
            false,
        );

        await applyThreadFilters(
            action.parameters.question,
            action.parameters.filters,
            options.threadSearch,
        );
        const response = await conversation.searchTermsV2(
            action.parameters.filters,
            searchOptions,
        );
        await adjustMessages(query, response, searchOptions, options);
        response.topKSettings = answers.settings.topK;
        if (!options.skipAnswerGeneration) {
            await generateAnswerForSearchTerms(query, response, options);
        }
        return response;
    }

    async function generateAnswer(
        query: string,
        actionResponse: SearchTermsActionResponse,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponse> {
        if (actionResponse.response) {
            await generateAnswerForSearchTerms(
                query,
                actionResponse.response,
                options,
            );
        }
        return actionResponse;
    }

    async function generateAnswerV2(
        query: string,
        actionResponse: SearchTermsActionResponseV2,
        options: SearchProcessingOptions,
    ): Promise<SearchTermsActionResponseV2> {
        if (actionResponse.action.actionName === "getAnswer") {
            query = actionResponse.action.parameters.question;
        }
        if (actionResponse.response) {
            await generateAnswerForSearchTerms(
                query,
                actionResponse.response,
                options,
            );
        }
        return actionResponse;
    }

    async function generateAnswerForSearchTerms(
        query: string,
        response: SearchResponse,
        options: SearchProcessingOptions,
        style?: AnswerStyle | undefined,
    ) {
        response.answer = await answers.generateAnswer(
            query,
            style,
            response,
            false,
        );
        if (response.answer?.type === "NoAnswer" && options.fallbackSearch) {
            await fallbackSearch(
                query,
                undefined,
                response,
                options.fallbackSearch,
            );
        }
    }

    function isTopicSummaryRequest(action: GetAnswerAction): boolean {
        const params = action.parameters;
        return (
            params.responseType === "Topics" &&
            !params.filters.some((f) => f.filterType !== "Topic")
        );
    }

    function isSummaryRequest(action: GetAnswerWithTermsAction): boolean {
        const filters = action.parameters.filters;
        for (const filter of filters) {
            if (filter.terms && filter.terms.length > 0) {
                return false;
            }
        }
        return true;
    }

    function isSummaryRequestV2(action: GetAnswerWithTermsActionV2): boolean {
        const filters = action.parameters.filters;
        for (const filter of filters) {
            if (
                filter.action ||
                (filter.searchTerms && filter.searchTerms.length > 0)
            ) {
                return false;
            }
        }
        return true;
    }

    function hasActionFilter(action: GetAnswerAction): boolean {
        const params = action.parameters;
        return !params.filters.some((f) => f.filterType !== "Action");
    }

    function ensureTopicFilter(query: string, filters: Filter[]): void {
        for (const filter of filters) {
            if (filter.filterType === "Topic") {
                if (filter.timeRange || filter.topics) {
                    return;
                }
                filter.topics ??= query;
                return;
            }
        }
        filters.push({
            filterType: "Topic",
            topics: query,
        });
    }

    function ensureEntityFilter(query: string, filters: Filter[]): void {
        for (const filter of filters) {
            if (filter.filterType === "Entity") {
                if (filter.timeRange || filter.name || filter.type) {
                    return;
                }
            }
        }
        filters.push({
            filterType: "Entity",
            name: query,
        });
    }

    function adjustRequest(
        query: string,
        action: GetAnswerAction,
        searchOptions: ConversationSearchOptions,
    ) {
        if (searchOptions.topic && searchOptions.topic.loadTopics) {
            ensureTopicFilter(
                isTopicSummaryRequest(action) ? "*" : query,
                action.parameters.filters,
            );
        }
        if (searchOptions.entity && searchOptions.entity.loadEntities) {
            ensureEntityFilter(query, action.parameters.filters);
        }
    }

    async function adjustResponse(
        query: string,
        action: GetAnswerAction,
        response: SearchResponse,
        options: ConversationSearchOptions,
        processingOptions: SearchProcessingOptions,
    ): Promise<void> {
        if (
            action.parameters.responseType == "Topics" &&
            !responseHasTopics(response)
        ) {
            await ensureEntitiesLoaded(response);
        }
        await adjustMessages(query, response, options, processingOptions);
    }

    async function adjustMessages(
        query: string,
        response: SearchResponse,
        options: ConversationSearchOptions,
        processingOptions: SearchProcessingOptions,
    ): Promise<void> {
        if (
            (!response.messages &&
                options.loadMessages &&
                processingOptions.fallbackSearch) ||
            (response.messages &&
                response.messages.length > processingOptions.maxMessages)
        ) {
            const result = await conversation.searchMessages(
                query,
                {
                    // No min score. We already know that the messages are relevant. We are using embeddings to pick the most relevant
                    maxMatches: processingOptions.maxMessages,
                },
                response.messageIds,
            );
            if (result) {
                response.messageIds = result.messageIds;
                response.messages = result.messages;
            } else if (response.messages) {
                response.messageIds = response.messageIds!.slice(
                    0,
                    processingOptions.maxMessages,
                );
                response.messages = response.messages.slice(
                    0,
                    processingOptions.maxMessages,
                );
            }
        }
    }

    async function ensureEntitiesLoaded(
        response: SearchResponse,
    ): Promise<void> {
        const entityIndex = await conversation.getEntityIndex();
        for (const result of response.entities) {
            if (result.entityIds && !result.entities) {
                result.entities = await entityIndex.getEntities(
                    result.entityIds,
                );
            }
        }
    }

    function responseHasTopics(response: SearchResponse): boolean {
        for (const _ of response.allTopics()) {
            return true;
        }
        return false;
    }

    async function fallbackSearch(
        query: string,
        style: ResponseStyle | undefined,
        response: SearchResponse,
        options: SearchOptions,
    ) {
        const sResult = await conversation.searchMessages(query, options);
        if (sResult) {
            response.fallbackUsed = true;
            response.messageIds = sResult.messageIds;
            response.messages = sResult.messages;
            response.answer = await answers.generateAnswer(
                query,
                style,
                response,
                true,
            );
        }
    }

    async function applyThreadFilters(
        query: string,
        filters: TermFilterV2[],
        options?: SearchOptions | undefined,
    ) {
        const threadIndex = await conversation.getThreadIndex();
        if (!options) {
            if (await threadIndex.matchTags(filters)) {
                options = { maxMatches: 1, minScore: 0.8 };
            }
        }
        if (options) {
            const threads = await threadIndex.getNearest(
                query,
                options.maxMatches,
                options.minScore,
            );
            if (threads.length === 0) {
                return;
            }
            const thread = threads[0];
            for (const filter of filters) {
                if (!filter.timeRange) {
                    filter.timeRange = thread.timeRange;
                }
            }
        }
    }

    function createSearchOptions(
        topLevelTopicSummary: boolean,
        options: SearchProcessingOptions,
        loadActions: boolean = false,
    ): ConversationSearchOptions {
        const topicLevel = topLevelTopicSummary ? 2 : 1;
        const topicOptions = createTopicSearchOptions(topLevelTopicSummary);
        topicOptions.minScore = options.minScore;
        const searchOptions: ConversationSearchOptions = {
            entity: options.entitySearch ??
                settings.defaultEntitySearchOptions ?? {
                    maxMatches: options.maxMatches,
                    minScore: options.minScore,
                    loadEntities: true,
                },
            topic: topicOptions,
            topicLevel,
            loadMessages: !topLevelTopicSummary,
        };
        searchOptions.action = {
            maxMatches: options.maxMatches,
            minScore: options.minScore,
            verbSearchOptions: {
                maxMatches: 1,
                minScore: options.minScore,
            },
            loadActions,
        };
        if (options.skipTopicSearch) {
            searchOptions.topic = undefined;
        }
        if (options.skipEntitySearch) {
            searchOptions.entity = undefined;
        }
        if (options.skipActionSearch) {
            searchOptions.action = undefined;
        }
        if (options.skipMessages) {
            searchOptions.loadMessages = false;
        }
        return searchOptions;
    }
}
