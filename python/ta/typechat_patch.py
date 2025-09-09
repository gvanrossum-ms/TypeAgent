# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Temporary patch for typechat module to provide missing classes for development."""

import typechat
from typing import TypeVar, Generic, Any

# Add missing classes to typechat module
T = TypeVar('T')

class Result(Generic[T]):
    """Temporary stub for typechat.Result"""
    def __init__(self, value: T | None = None, error: str | None = None):
        self.value = value
        self.error = error

class Failure:
    """Temporary stub for typechat.Failure"""
    def __init__(self, message: str = ""):
        self.message = message

class Success(Generic[T]):
    """Temporary stub for typechat.Success"""
    def __init__(self, value: T):
        self.value = value

class TypeChatLanguageModel:
    """Temporary stub for typechat.TypeChatLanguageModel"""
    def __init__(self):
        pass

class PromptSection:
    """Temporary stub for typechat.PromptSection"""
    def __init__(self):
        pass

# Patch the typechat module
typechat.Result = Result
typechat.Failure = Failure  
typechat.Success = Success
typechat.TypeChatLanguageModel = TypeChatLanguageModel
typechat.PromptSection = PromptSection