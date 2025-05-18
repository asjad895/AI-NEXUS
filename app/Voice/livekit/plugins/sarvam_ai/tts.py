# Copyright 2023 LiveKit, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import asyncio
import base64
import os
from dataclasses import dataclass
from typing import Any, List, Optional

import aiohttp

from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tts,
    utils,
)
from livekit.agents.types import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)
from livekit.agents.utils import is_given

from .log import logger
from .models import TTSLanguageCodes, TTSSpeakers, TTSModels

DEFAULT_BASE_URL = "https://api.sarvam.ai"
DEFAULT_SPEAKER = "Meera"
DEFAULT_MODEL = "bulbul:v2"
DEFAULT_SAMPLE_RATE = 22050
NUM_CHANNELS = 1


@dataclass
class _TTSOptions:
    model: TTSModels | str
    target_language_code: TTSLanguageCodes | str
    speaker: TTSSpeakers | str
    api_key: str
    base_url: str
    pitch: NotGivenOr[float]
    pace: NotGivenOr[float]
    loudness: NotGivenOr[float]
    speech_sample_rate: int
    enable_preprocessing: bool


class TTS(tts.TTS):
    def __init__(
        self,
        *,
        base_url: NotGivenOr[str] = NOT_GIVEN,
        model: TTSModels | str = DEFAULT_MODEL,
        target_language_code: TTSLanguageCodes | str = "en-IN",
        speaker: TTSSpeakers | str = DEFAULT_SPEAKER,
        pitch: NotGivenOr[float] = NOT_GIVEN,
        pace: NotGivenOr[float] = NOT_GIVEN,
        loudness: NotGivenOr[float] = NOT_GIVEN,
        speech_sample_rate: int = DEFAULT_SAMPLE_RATE,
        enable_preprocessing: bool = False,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        """
        Create a new instance of Sarvam TTS.

        If `api_key` is not provided, it will be read from the ``SARVAM_API_KEY``
        environmental variable.

        Args:
            model (TTSModels | str, optional): Model to use. Default is "bulbul:v2".
            target_language_code (TTSLanguageCodes | str, optional): Target language in BCP-47 format. Default is "en-IN".
            speaker (TTSSpeakers | str, optional): Voice to use. Default is "Meera".
            pitch (float, optional): Controls the pitch of the audio (-0.75 to 0.75). Default is 0.0.
            pace (float, optional): Controls the speed of the audio (0.5 to 2.0). Default is 1.0.
            loudness (float, optional): Controls the loudness of the audio (0.3 to 3.0). Default is 1.0.
            speech_sample_rate (int, optional): Sample rate (8000, 16000, 22050, 24000). Default is 22050.
            enable_preprocessing (bool, optional): Enable normalization of English words and numeric entities.
            api_key (str, optional): API key to use.
            base_url (str, optional): Base URL for the Sarvam API.
            http_session (aiohttp.ClientSession, optional): HTTP session to use.
        """

        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=False, 
            ),
            sample_rate=speech_sample_rate,
            num_channels=NUM_CHANNELS,
        )

        self._session = http_session

        if not is_given(base_url):
            base_url = DEFAULT_BASE_URL

        sarvam_api_key = api_key if is_given(api_key) else os.getenv("SARVAM_API_KEY")
        if not sarvam_api_key:
            raise ValueError("SARVAM_API_KEY is not set")

        self._opts = _TTSOptions(
            model=model,
            target_language_code=target_language_code,
            speaker=speaker,
            api_key=sarvam_api_key,
            base_url=base_url,
            pitch=pitch,
            pace=pace,
            loudness=loudness,
            speech_sample_rate=speech_sample_rate,
            enable_preprocessing=enable_preprocessing,
        )

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()

        return self._session

    def update_options(
        self,
        *,
        model: NotGivenOr[TTSModels | str] = NOT_GIVEN,
        target_language_code: NotGivenOr[TTSLanguageCodes | str] = NOT_GIVEN,
        speaker: NotGivenOr[TTSSpeakers | str] = NOT_GIVEN,
        pitch: NotGivenOr[float] = NOT_GIVEN,
        pace: NotGivenOr[float] = NOT_GIVEN,
        loudness: NotGivenOr[float] = NOT_GIVEN,
        speech_sample_rate: NotGivenOr[int] = NOT_GIVEN,
        enable_preprocessing: NotGivenOr[bool] = NOT_GIVEN,
    ) -> None:
        """
        Update the TTS options.

        Args:
            model (TTSModels | str, optional): Model to use.
            target_language_code (TTSLanguageCodes | str, optional): Target language in BCP-47 format.
            speaker (TTSSpeakers | str, optional): Voice to use.
            pitch (float, optional): Controls the pitch of the audio (-0.75 to 0.75).
            pace (float, optional): Controls the speed of the audio (0.5 to 2.0).
            loudness (float, optional): Controls the loudness of the audio (0.3 to 3.0).
            speech_sample_rate (int, optional): Sample rate (8000, 16000, 22050, 24000).
            enable_preprocessing (bool, optional): Enable normalization of English words and numeric entities.
        """
        if is_given(model):
            self._opts.model = model
        if is_given(target_language_code):
            self._opts.target_language_code = target_language_code
        if is_given(speaker):
            self._opts.speaker = speaker
        if is_given(pitch):
            self._opts.pitch = pitch
        if is_given(pace):
            self._opts.pace = pace
        if is_given(loudness):
            self._opts.loudness = loudness
        if is_given(speech_sample_rate):
            self._opts.speech_sample_rate = speech_sample_rate
        if is_given(enable_preprocessing):
            self._opts.enable_preprocessing = enable_preprocessing

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> ChunkedStream:
        return ChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            opts=self._opts,
            session=self._ensure_session(),
        )


class ChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: TTS,
        input_text: str,
        conn_options: APIConnectOptions,
        opts: _TTSOptions,
        session: aiohttp.ClientSession,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._opts = opts
        self._session = session

    async def _run(self) -> None:
        request_id = utils.shortuuid()
        headers = {
            "api-subscription-key": self._opts.api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": self._input_text,
            "target_language_code": self._opts.target_language_code,
            "speaker": self._opts.speaker,
            "model": self._opts.model,
            "speech_sample_rate": self._opts.speech_sample_rate,
            "enable_preprocessing": self._opts.enable_preprocessing,
        }
        
        if is_given(self._opts.pitch):
            payload["pitch"] = self._opts.pitch
        if is_given(self._opts.pace):
            payload["pace"] = self._opts.pace
        if is_given(self._opts.loudness):
            payload["loudness"] = self._opts.loudness

        decoder = utils.codecs.AudioStreamDecoder(
            sample_rate=self._opts.speech_sample_rate,
            num_channels=NUM_CHANNELS,
        )

        api_url = f"{self._opts.base_url}/text-to-speech"
        try:
            async with self._session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(connect=self._conn_options.timeout, total=30),
            ) as response:
                if response.status != 200:
                    content = await response.text()
                    logger.error("Sarvam returned error: %s", content)
                    raise APIStatusError(
                        message=content,
                        status_code=response.status,
                        request_id=request_id,
                        body=content,
                    )

                response_json = await response.json()
                audio_base64 = response_json.get("audios", [])[0]
                
                if not audio_base64:
                    logger.error("No audio data in Sarvam response")
                    return
                
                audio_data = base64.b64decode(audio_base64)
                decoder.push(audio_data)
                decoder.end_input()
                
                emitter = tts.SynthesizedAudioEmitter(
                    event_ch=self._event_ch,
                    request_id=request_id,
                )
                
                async for frame in decoder:
                    emitter.push(frame)
                emitter.flush()

        except asyncio.TimeoutError as e:
            raise APITimeoutError() from e
        except aiohttp.ClientResponseError as e:
            raise APIStatusError(
                message=e.message,
                status_code=e.status,
                request_id=request_id,
                body=None,
            ) from e
        except Exception as e:
            raise APIConnectionError() from e
        finally:
            await decoder.aclose()