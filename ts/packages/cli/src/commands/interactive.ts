// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import { Args, Command, Flags } from "@oclif/core";
import { createDispatcher, Dispatcher } from "agent-dispatcher";
import {
    createActionConfigProvider,
    getCacheFactory,
    getInstanceDir,
    getSchemaNamesForActionConfigProvider,
} from "agent-dispatcher/internal";
import {
    getDefaultAppAgentProviders,
    getDefaultConstructionProvider,
    getDefaultAppAgentInstaller,
} from "default-agent-provider";
import inspector from "node:inspector";
import { getChatModelNames } from "aiclient";
import {
    processCommands,
    withConsoleClientIO,
} from "agent-dispatcher/helpers/console";

const modelNames = await getChatModelNames();
const instanceDir = getInstanceDir();
const defaultAppAgentProviders = getDefaultAppAgentProviders(instanceDir);
const schemaNames = getSchemaNamesForActionConfigProvider(
    await createActionConfigProvider(defaultAppAgentProviders),
);
export default class Interactive extends Command {
    static description = "Interactive mode";
    static flags = {
        schema: Flags.string({
            description: "Schema names",
            options: schemaNames,
            multiple: true,
        }),
        explainer: Flags.string({
            description:
                "Explainer name (defaults to the explainer associated with the translator)",
            options: getCacheFactory().getExplainerNames(),
        }),
        model: Flags.string({
            description: "Translation model to use",
            options: modelNames,
        }),
        debug: Flags.boolean({
            description: "Enable debug mode",
            default: false,
        }),
        memory: Flags.boolean({
            description: "In memory session",
            default: false,
        }),
        exit: Flags.boolean({
            description: "Exit after processing input file",
            default: true,
            allowNo: true,
        }),
    };
    static args = {
        input: Args.file({
            description:
                "A text input file containing one interactive command per line",
            exists: true,
        }),
    };
    async run(): Promise<void> {
        const { args, flags } = await this.parse(Interactive);

        if (flags.debug) {
            inspector.open(undefined, undefined, true);
        }

        const schemas = flags.schema
            ? Object.fromEntries(flags.schema.map((name) => [name, true]))
            : undefined;

        await withConsoleClientIO(async (clientIO) => {
            const dispatcher = await createDispatcher("cli interactive", {
                appAgentProviders: defaultAppAgentProviders,
                agentInstaller: getDefaultAppAgentInstaller(instanceDir),
                schemas,
                translation: { model: flags.model },
                explainer: { name: flags.explainer },
                persistSession: !flags.memory,
                enableServiceHost: true,
                clientIO,
                dblogging: true,
                constructionProvider: getDefaultConstructionProvider(),
            });
            try {
                if (args.input) {
                    await dispatcher.processCommand(`@run ${args.input}`);
                    if (flags.exit) {
                        return;
                    }
                }

                await processCommands(
                    () => dispatcher.getPrompt(),
                    (command: string, dispatcher: Dispatcher) =>
                        dispatcher.processCommand(command),
                    dispatcher,
                );
            } finally {
                if (dispatcher) {
                    await dispatcher.close();
                }
            }
        });

        // Some background network (like mongo) might keep the process live, exit explicitly.
        process.exit(0);
    }
}
