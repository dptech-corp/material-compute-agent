# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
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
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
from typing import Any, Dict

from camel_sci.prompts.ai_society import (
    AISocietyPromptTemplateDict,
    TextPromptDict,
)
from camel_sci.prompts.code import CodePromptTemplateDict
from camel_sci.prompts.evaluation import (
    EvaluationPromptTemplateDict,
)
from camel_sci.prompts.generate_text_embedding_data import (
    GenerateTextEmbeddingDataPromptTemplateDict,
)
from camel_sci.prompts.image_craft import ImageCraftPromptTemplateDict
from camel_sci.prompts.misalignment import MisalignmentPromptTemplateDict
from camel_sci.prompts.multi_condition_image_craft import (
    MultiConditionImageCraftPromptTemplateDict,
)
from camel_sci.prompts.object_recognition import (
    ObjectRecognitionPromptTemplateDict,
)
from camel_sci.prompts.role_description_prompt_template import (
    RoleDescriptionPromptTemplateDict,
)
from camel_sci.prompts.solution_extraction import (
    SolutionExtractionPromptTemplateDict,
)
from camel_sci.prompts.translation import TranslationPromptTemplateDict
from camel_sci.prompts.video_description_prompt import (
    VideoDescriptionPromptTemplateDict,
)
from camel_sci.types import TaskType


class TaskPromptTemplateDict(Dict[Any, TextPromptDict]):
    r"""A dictionary (:obj:`Dict[Any, TextPromptDict]`) of task prompt
    templates keyed by task type. This dictionary is used to map from
    a task type to its corresponding prompt template dictionary.

    Args:
        *args: Positional arguments passed to the :obj:`dict` constructor.
        **kwargs: Keyword arguments passed to the :obj:`dict` constructor.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            {
                TaskType.AI_SOCIETY: AISocietyPromptTemplateDict(),
                TaskType.CODE: CodePromptTemplateDict(),
                TaskType.MISALIGNMENT: MisalignmentPromptTemplateDict(),
                TaskType.TRANSLATION: TranslationPromptTemplateDict(),
                TaskType.EVALUATION: EvaluationPromptTemplateDict(),
                TaskType.SOLUTION_EXTRACTION: SolutionExtractionPromptTemplateDict(),  # noqa: E501
                TaskType.ROLE_DESCRIPTION: RoleDescriptionPromptTemplateDict(),
                TaskType.OBJECT_RECOGNITION: ObjectRecognitionPromptTemplateDict(),  # noqa: E501
                TaskType.GENERATE_TEXT_EMBEDDING_DATA: GenerateTextEmbeddingDataPromptTemplateDict(),  # noqa: E501
                TaskType.IMAGE_CRAFT: ImageCraftPromptTemplateDict(),
                TaskType.MULTI_CONDITION_IMAGE_CRAFT: MultiConditionImageCraftPromptTemplateDict(),  # noqa: E501
                TaskType.VIDEO_DESCRIPTION: VideoDescriptionPromptTemplateDict(),  # noqa: E501
            }
        )
