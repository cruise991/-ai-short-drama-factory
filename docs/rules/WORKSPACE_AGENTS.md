# Auto-Media Project Rules

## 1. Orchestration & Project Structure
- **Dynamic Projects**: The orchestrator must always create new projects under `projects/<slugified_goal>/`. Never hardcode `episode-01` or any static directory for new tasks.
- **Output Routing**: Final rendered media MUST be isolated and moved to `out/<slugified_goal>/`. Intermediate assets remain in `projects/<slugified_goal>/runs/`.
- **Deadlock Prevention**: The orchestrator must track consecutive failures (`Drafting`, `Draft_Completed`). If a specific state fails ≥3 times consecutively, it must trigger a `Paused_By_Error` to halt the infinite loop and request human intervention.

## 2. Planning Department Interaction
- **Interactive Multi-Turn Consulting**: The planning agent (`planning_agent.py`) must use a multi-turn chat interaction loop in the terminal. It should read `trending_research`, offer advice, and wait for user input until the user types `ok` or `confirm`. Do NOT use a rigid fixed-question prompt.
- **QA Feedback Adherence**: When receiving `qa_feedback`, the planning agent must inject a high-priority, heavily emphasized block (e.g., `<CRITICAL_CORRECTION>`) at the end of the storyboard prompt to force the LLM to obey the QA rules and prevent deadlock.

## 3. Data Acqusition (Trending)
- Always use the valid CLI arguments for tools like `last30days.py` (e.g., `--quick` instead of `--limit 3`).
- If LLM fallback is needed, the LLM must be explicitly instructed to hallucinate/simulate realistic data if it cannot access the internet, preventing it from outputting generic refusal messages ("As an AI assistant...").

## 4. Autonomous Evolution & Memory System (V4)
- **Market-Driven Evolution**: The system MUST implement a closed-loop market feedback state (`Market_Testing`). `feedback_agent.py` must simulate or fetch real-world performance data (views, completion rate, conversion rate) to extract Positive and Negative Marketing Patterns.
- **Knowledge Distillation**: When fetching trending research, `planning_agent.py` MUST dynamically distill a single, high-impact structural rule from the raw data and enforce it in the script generation prompt, ensuring real-time learning rather than static copying.
- **Semantic Compression & Executive Override**: Do NOT use simple FIFO list truncation for memory management. `qa_agent.py` must use LLM-driven Semantic Compression to merge redundant rules, keeping the rule count under 5. Rules prefixed with `[CEO]` hold the highest executive authority and must NEVER be overwritten or diluted during compression.

## 5. Artifact Output Language
- ALL artifact documents (including `walkthrough.md`, `implementation_plan.md`, `task.md`, etc.) MUST be written entirely in Simplified Chinese (简体中文).

## 6. Git Repositories
- **Private Backup / Active Development**: `https://github.com/cruise991/ai-short-drama` (Remote: `origin`) - Use this for regular backups and Web UI refactoring.
- **Open Source Release**: `https://github.com/cruise991/-ai-short-drama-factory` (Remote: `opensource`) - Only push sanitized, safe, and curated code here. No sensitive keys.

## 7. Agnes Image 2.5 Flash API Specification & Usage Rules
- **Model Name**: `agnes-image-2.5-flash` (Must be spelled exactly).
- **Pricing & Quota**: `agnes-image-2.0-flash`、`agnes-image-2.1-flash` 和 `agnes-image-2.5-flash` 的价格及计费方法相同。当前所有输出分辨率档位和输入参考图片均免费，统一采用 `agnes-image-2.5-flash`。
- **Endpoint**: `POST https://apihub.agnes-ai.com/v1/images/generations`
- **Headers**: `Authorization: Bearer YOUR_API_KEY`, `Content-Type: application/json`
- **Schema & Parameters**:
  - `model`: String (Required) = `"agnes-image-2.5-flash"`
  - `prompt`: String (Required) = Prompt text
  - `size`: String (Required) = Preset size (`"1K"`, `"2K"`, `"3K"`, `"4K"`). Do NOT pass raw pixels like `"1920x1080"`.
  - `ratio`: String (Optional) = Aspect ratio (`"1:1"`, `"3:4"`, `"4:3"`, `"16:9"`, `"9:16"`, `"2:3"`, `"3:2"`, `"21:9"`). Default: `"1:1"`.
  - `return_base64`: Boolean (Optional) = **Text-to-Image ONLY**: Set `true` for base64 output.
  - `extra_body`: Object (Optional) = Advanced parameter object.
    - `extra_body.image`: Array[String] = **Image-to-Image / Multi-Image Blend ONLY**: Array of public URLs or Base64 Data URIs.
    - `extra_body.response_format`: String = Output format (`"url"` or `"b64_json"`). **Image-to-Image base64 MUST use this parameter.**
- **CRITICAL RULES & AUDIT MANDATES**:
  1. **`response_format` MUST be nested inside `extra_body`**, NEVER at top-level.
  2. **Do NOT pass `tags: ["img2img"]`** in Image-to-Image mode; passing `extra_body.image` triggers it automatically.
  3. **Return format parameter rules**:
     - Text-to-Image Base64: Top-level `return_base64: true`.
     - Image-to-Image Base64: Nested `extra_body.response_format: "b64_json"`.
  4. **Size parameter rules**: Request `size: "2K"` and `ratio: "16:9"` (not raw pixel strings like `1920x1080`).
  5. Every code update or configuration edit related to Agnes Image generation MUST be checked against this specification.

## 8. Agnes Video 2.5 Flash API Specification & Usage Rules
- **Model Name**: `agnes-video-2.5-flash` (Must be spelled exactly).
- **Pricing & Quota**: `agnes-video-2.5-flash` 采用与 `agnes-video-2.5` 相同的计费公式，当前限时免费，统一采用 `agnes-video-2.5-flash`。
  - 标准计费规则：按输出视频分辨率和总计费时长计费；总计费时长为输出视频时长与输入视频时长之和。输入图片前 5 张免费，第 6 张起按 $0.005 / 张 计费。
- **Workflow Mechanism**: Asynchronous 2-Step Workflow (Task Creation POST -> Status Polling GET).
- **Endpoints**:
  - **Step 1: Task Creation (POST)**: `POST https://apihub.agnes-ai.com/v1/videos`
  - **Step 2: Status Polling (GET)**: `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash`
  - **Headers**: `Authorization: Bearer YOUR_API_KEY`, `Content-Type: application/json`
- **Schema & Parameters**:
  - `model`: String (Required) = `"agnes-video-2.5-flash"`
  - `prompt`: String (Required) = Prompt instructions
  - `mode`: String (Required) = `"keyframe"` (for start/end frame control), `"text"`, or `"reference"`.
  - `first_frame`: String (Optional) = Public image URL for the starting frame. Required for `mode: "keyframe"`.
  - `last_frame`: String (Optional) = Public image URL for the ending frame (loop closure).
  - `seconds`: String (Optional) = Video duration string (`"4"` – `"12"`, default `"5"`).
  - `size`: String (Optional) = Output resolution (`"720P"`, `"1080P"`, `"1K"`, `"2K"`, default `"720P"`).
  - `aspect_ratio`: String (Optional) = Aspect ratio (`"9:16"`, `"16:9"`, etc.).
- **CRITICAL RULES & AUDIT MANDATES**:
  1. **Strict `mode` rule**: `mode` is required and must be `"keyframe"` (when providing initial/terminal frames), `"text"`, or `"reference"`. Do NOT pass raw width/height pixels.
  2. **Image parameter location rules (CRITICAL)**:
     - Starting keyframe: Top-level `first_frame: "url"`.
     - Ending keyframe: Top-level `last_frame: "url"`.
  3. **Asynchronous Polling Rule**: Creation POST returns `video_id`. Must poll GET endpoint `https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash` until `status == "completed"`, then extract output URL from `url`.
  4. Every code update or configuration edit related to Agnes Video generation MUST be audited against this specification.

## 9. Agnes 3.0 Flash LLM Specification & Usage Rules
- **Model Name**: `agnes-3.0-flash` (Must be spelled exactly).
- **Context & Pricing**: Input cache hit, input tokens, and output tokens are currently free.
- **Endpoints**:
  - **Chat Completions (Recommended)**: `POST https://apihub.agnes-ai.com/v1/chat/completions`
  - **Responses API (Extended)**: `POST https://apihub.agnes-ai.com/v1/responses`
  - **Headers**: `Authorization: Bearer YOUR_API_KEY`, `Content-Type: application/json`
- **CRITICAL RULES & AUDIT MANDATES**:
  1. **Vision / Multimodal Input Rule**: Image inputs MUST use public `image_url` within array payload: `content: [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "https://..."}}]`.
  2. **Responses API Output Parsing Rule (CRITICAL)**: NO top-level `output_text` field exists in Responses API. Parsing path MUST be: `output` array -> find `type == "message"` -> find `content` item `type == "output_text"` -> extract `text`.
  3. **Token Limit Parameter Rules**: Use `max_tokens` for Chat Completions; use `max_output_tokens` for Responses API.
  4. **Thinking Mode Configuration Rules**:
     - OpenAI format: `chat_template_kwargs: { "enable_thinking": true }`
     - Anthropic format: `thinking: { "type": "enabled", "budget_tokens": 2048 }`
  5. Every code update or LLM API integration for prompt/script generation MUST be checked against this specification.

## 10. Agnes 2.5 Flash LLM (Fallback) Specification & Usage Rules
- **Model Name**: `agnes-2.5-flash` (Must be spelled exactly).
- **Context & Pricing**: Input cache hit, input tokens, and output tokens are currently free. Official fallback model for `agnes-3.0-flash` during instability.
- **Endpoints**:
  - **Chat Completions (Recommended)**: `POST https://apihub.agnes-ai.com/v1/chat/completions`
  - **Headers**: `Authorization: Bearer YOUR_API_KEY`, `Content-Type: application/json`
- **CRITICAL RULES & AUDIT MANDATES**:
  1. **Fallback Switch Rule**: When `agnes-3.0-flash` encounters timeouts or instability, fallback logic MUST seamlessly switch `model` to `"agnes-2.5-flash"`.
  2. **Vision / Multimodal Input Rule**: Image inputs MUST use public `image_url` within array payload.
  3. Every code update or LLM API fallback implementation MUST be checked against this specification.




