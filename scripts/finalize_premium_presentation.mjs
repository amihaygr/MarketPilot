import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(scriptDir, "..");
const { SKILL_DIR: skillDir, RUNTIME_PYTHON: pythonExecutable } = process.env;
if (!path.isAbsolute(skillDir ?? "") || !path.isAbsolute(pythonExecutable ?? "")) {
  throw new Error("Set absolute SKILL_DIR and RUNTIME_PYTHON paths");
}
const buildDir = path.join(workspaceDir, ".presentation-build", "premium");
const candidatePath = path.join(buildDir, "MarketPilot-premium-candidate.pptx");
const finalPath = path.join(
  workspaceDir,
  "docs",
  "presentation",
  "output",
  "MarketPilot-Final-Presentation.pptx",
);
const receiptPath = path.join(buildDir, "MarketPilot-Final-Presentation.validation.json");
await fs.mkdir(path.dirname(finalPath), { recursive: true });

const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href
);

const result = await finalizePresentation({
  explicitTotalSlideCount: 12,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable,
  integrityValidatorPath: path.join(
    skillDir,
    "container_tools",
    "inspect_presentation_package_integrity.py",
  ),
  layoutValidatorPath: path.join(
    skillDir,
    "container_tools",
    "inspect_presentation_layout_geometry.py",
  ),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  fontPolicy: {
    basis: "design",
    families: ["Segoe UI", "Cascadia Mono"],
  },
  verifyArtifactToolImport: true,
  receiptPath,
});

console.log(JSON.stringify({ finalPath, receiptPath, result }, null, 2));
