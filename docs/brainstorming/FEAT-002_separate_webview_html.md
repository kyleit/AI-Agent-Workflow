# Brainstorming: FEAT-002_separate_webview_html

| 🔒 DISCOVERY MODE ACTIVE |
| :--- |
| This Skill is running in **READ-ONLY / DISCOVERY ONLY** mode. |
| I will **NOT** modify any source code. |
| I will **NOT** edit any project files. |
| I will **NOT** implement anything. |
| I will **ONLY** perform Requirement Discovery. |
| The ONLY file I may write is: `docs/brainstorm/FEAT-XXX_feature_name.md` |
| And ONLY after explicit user confirmation (Y/N). |

---

## 🎯 Requirements & Decomposition

**Goal**: Separate the inline HTML string (approx. 700 lines) from `extensions/visualizer/src/extension.ts` into a standalone template file for cleaner maintenance and auto-formatting/syntax highlighting in IDEs.

**Proposed Feature**:
- Extract the HTML template (with embedded CSS and JavaScript) to `extensions/visualizer/resources/webview.html`.
- Automate the build compilation process to inline this HTML into the compiled TypeScript code (Option 2).

---

## 🛠️ Proposed Solution (Statically Compiled Code-Gen)

To achieve static inlining without complex bundlers (like webpack/esbuild) and maintain compatibility with `tsc`, we will implement a code-generation build script:

1. **Source Template**:
   `extensions/visualizer/resources/webview.html`
2. **Build Script** (`extensions/visualizer/build.js`):
   A small Node.js script that reads `resources/webview.html`, escapes backticks and backslashes, and writes it as a static TypeScript export:
   ```typescript
   // src/webviewHtml.ts (Auto-generated)
   export const webviewHtml = `...`;
   ```
3. **Usage in `extension.ts`**:
   ```typescript
   import { webviewHtml } from './webviewHtml';
   
   private getHtmlContent(): string {
       return webviewHtml;
   }
   ```
4. **Compilation Pipeline**:
   Update `package.json` compilation script:
   ```json
   "compile": "node build.js && tsc -p ./"
   ```

---

## 🚦 Next Phase Recommended
- Run `/plan` to convert this brainstorming document into a formal Implementation Plan (`docs/plans/FEAT-002_separate_webview_html_plan.md`).
