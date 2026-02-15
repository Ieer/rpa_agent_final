# Pydantic-AI 工具整合改造待辦（評估版）

## 背景
- 現行 chat 到工具調用主要依賴模型是否產生 tool call，小模型情境下穩定性不足。
- 採漸進式改造：先做 S1（工具層增強），後續再評估 S2（聊天入口半替換）。

## 目標
- 強化工具參數驗證、錯誤分類、可觀測性與可回滾能力。
- 保持 `adapter/chat_service.py` 與 `core/executor.py` 主流程穩定。

## 逐檔待辦（目的 + 驗收）

### 1) nanobot_tool.py
- 目的：`execute_rpa` 入參型別化驗證（feature flag 控制）。
- 驗收：
  - 合法參數可成功執行。
  - 缺參數/型別錯誤有結構化回傳。
  - 關閉 flag 時行為與舊版一致。

### 2) nanobot/nanobot/agent/tools/registry.py
- 目的：工具驗證與執行錯誤分類（validation/runtime）。
- 驗收：
  - 可區分參數錯誤與執行錯誤。
  - 既有工具不受影響。

### 3) nanobot/nanobot/agent/tools/base.py
- 目的：新舊驗證雙軌相容。
- 驗收：
  - legacy 驗證用例不退化。
  - 新驗證分支可運作。

### 4) config.yaml
- 目的：新增工具引擎 feature flag。
- 驗收：
  - 缺省配置不報錯且默認 legacy。
  - 可一鍵切回 legacy。

### 5) requirements.txt
- 目的：加入 `pydantic-ai`（後續階段）。
- 驗收：
  - 依賴可安裝且不衝突。

### 6) tests/test_nanobot_tool.py
- 目的：補 execute_rpa 驗證路徑測試。
- 驗收：
  - 覆蓋成功、缺參數、型別錯、RPA 不存在。

### 7) nanobot/tests/test_tool_validation.py
- 目的：框架層回歸測試。
- 驗收：
  - 新舊路徑均通過。

### 8) adapter/chat_service.py（建議）
- 目的：加入最小可觀測欄位（run_id/tool/error_type/duration）。
- 驗收：
  - 可依 run_id 回溯工具調用結果。

### 9) adapter/api.py（建議）
- 目的：在 status 回傳擴展觀測欄位（向後相容）。
- 驗收：
  - 舊前端不需修改即可運行。

### 10) tests/test_api.py（建議）
- 目的：驗證新增欄位相容性。
- 驗收：
  - 原有 API 測試不退化。

## 評估指標（A/B）
- 工具成功率
- 參數驗證失敗率
- 平均延遲與 P95
- 回滾成功率

## 完成定義（DoD）
- 最小集完成後可用 feature flag 安全切換。
- 測試全綠，無既有流程回歸。
- 評估指標可觀測且可比較。