# 数字人角色与声音授权元数据规范 (Avatar & Voice Licensing Spec)

## 一、概述
为彻底规避数字人形象侵权、肖像权纠纷及合规风险，系统内所有用于短剧制作与实时直播的数字人角色、声音模型，必须在数据库与资源配置文件中强制附带标准化合规元数据。

---

## 二、元数据 Schema 规范 (JSON / Database)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AvatarLicensingMetadata",
  "type": "object",
  "required": [
    "avatar_id",
    "name",
    "category",
    "source_type",
    "commercial_permitted",
    "watermark_mandatory"
  ],
  "properties": {
    "avatar_id": {
      "type": "string",
      "description": "数字人唯一标识符，格式规范: avt_[分类]_[标识]",
      "example": "avt_original_sophia_01"
    },
    "name": {
      "type": "string",
      "description": "角色展示名称",
      "example": "索菲亚 (Sophia)"
    },
    "category": {
      "type": "string",
      "enum": ["anchor", "actor", "game_npc", "narrator"],
      "description": "角色定位类型: 主播 / 短剧演员 / NPC / 旁白"
    },
    "source_type": {
      "type": "string",
      "enum": ["original_ai", "authorized_human", "public_domain", "licensed_ip"],
      "description": "资产来源: AI原创 / 真人授权孪生 / 公有领域 / 商业授权IP"
    },
    "commercial_permitted": {
      "type": "boolean",
      "description": "是否已获得合法商用授权，如未获得则系统禁止开启商用直播"
    },
    "authorization_contract_no": {
      "type": "string",
      "description": "关联的法律授权协议书编号，若为真人授权必须提供",
      "example": "AUTH-2026-AVT-0042"
    },
    "authorization_valid_until": {
      "type": "string",
      "format": "date",
      "description": "授权到期时间 (ISO 8601 YYYY-MM-DD)，若过期系统自动冻结该形象",
      "example": "2028-12-31"
    },
    "voice_profile": {
      "type": "object",
      "required": ["provider", "voice_id", "commercial_permitted"],
      "properties": {
        "provider": {
          "type": "string",
          "enum": ["kokoro", "gpt_sovits", "edge_tts", "custom_tts"],
          "description": "TTS 服务提供商"
        },
        "voice_id": {
          "type": "string",
          "description": "模型声音 ID 或音色名称"
        },
        "commercial_permitted": {
          "type": "boolean",
          "description": "声音商用许可状态"
        }
      }
    },
    "watermark_mandatory": {
      "type": "boolean",
      "default": true,
      "description": "是否强制渲染 AI 数字人合规角标与水印"
    },
    "disclaimer_text": {
      "type": "string",
      "default": "虚拟数字人播报，由 AI 技术合成",
      "description": "合成视频底端强制显示的免责提示文字"
    }
  }
}
```

---

## 三、系统准入拦截策略 (Phase 2 集成规则)

1. **未合规资产阻断**：
   - 当 `commercial_permitted == false` 时，如果用户选择用于商业直播流或计费生产，后端控制器必须直接拒绝并报错：`HTTP 403: Avatar not authorized for commercial usage`。
2. **授权过期自动下架**：
   - 调度系统定期轮询数字人元数据，若当前时间超过 `authorization_valid_until`，状态自动置为 `Suspended`，禁止推流。
3. **强制水印不可绕过**：
   - 无论前端传入何种参数，只要 `watermark_mandatory == true`，推流与合成管道中的 FFMPEG 过滤器必须强制叠加合规水印滤镜。
