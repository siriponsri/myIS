/*
 * Hallmark -- macrostructure: Long Document; theme: Studio; tone: technical editorial.
 * Hallmark -- pre-emit critique: P5 H5 E5 S5 R5 V4.
 *
 * Builds the advisor deck from docs/presentation/material.  Run this module from an
 * artifact-tool workspace after rasterizing the listed SVG source figures.
 */

import fs from "node:fs/promises";
import path from "node:path";

import { Presentation, PresentationFile } from "@oai/artifact-tool";

const PAGE = { width: 1280, height: 720 };
const FRAME = { left: 72, top: 54, width: 1136, height: 612 };
const FONT_DISPLAY = "Cambria";
const FONT_BODY = "Aptos";
const C = {
  paper: "#F7FAF9",
  ink: "#172027",
  muted: "#52606D",
  line: "#DCE5E2",
  teal: "#0F766E",
  tealSoft: "#D8F0EB",
  gold: "#C18119",
  goldSoft: "#FFF1CC",
  coral: "#B95059",
  coralSoft: "#F8E5E6",
  white: "#FFFFFF",
};

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) throw new Error(`Unexpected positional argument: ${key}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      args[key.slice(2)] = true;
      continue;
    }
    args[key.slice(2)] = value;
    index += 1;
  }
  return args;
}

function required(args, key) {
  const value = args[key];
  if (typeof value !== "string" || value.length === 0) throw new Error(`Missing --${key}`);
  return path.resolve(value);
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function box(slide, { name, left, top, width, height, fill = "none", line = "none", radius = 0 }) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    name,
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function text(slide, {
  name,
  value,
  left,
  top,
  width,
  height,
  size = 24,
  face = FONT_BODY,
  color = C.ink,
  bold = false,
  align = "left",
  valign = "top",
  lineSpacing = 1.12,
  fill = "none",
  insets = { left: 0, right: 0, top: 0, bottom: 0 },
}) {
  const shape = box(slide, { name, left, top, width, height, fill });
  shape.text = value;
  shape.text.style = {
    fontSize: size,
    typeface: face,
    color,
    bold,
    alignment: align,
    verticalAlignment: valign,
    lineSpacing,
    autoFit: "none",
    wrap: "square",
    insets,
  };
  return shape;
}

function rule(slide, left, top, width, color = C.teal, height = 4) {
  return box(slide, { name: "rule", left, top, width, height, fill: color });
}

function addNotes(slide, note, sources) {
  slide.speakerNotes.textFrame.setText(`${note}\n\n[Sources]\n${sources.join("\n")}`);
  slide.speakerNotes.setVisible(true);
}

function addChrome(slide, section, slideNumber, total) {
  slide.background.fill = "bg1";
  text(slide, {
    name: "section-label",
    value: section.toUpperCase(),
    left: FRAME.left,
    top: 30,
    width: 500,
    height: 18,
    size: 14,
    color: C.teal,
    bold: true,
  });
  rule(slide, FRAME.left, 48, FRAME.width, C.line, 1);
  text(slide, {
    name: "slide-number",
    value: `${String(slideNumber).padStart(2, "0")} / ${String(total).padStart(2, "0")}`,
    left: 1114,
    top: 678,
    width: 94,
    height: 18,
    size: 14,
    color: C.muted,
    align: "right",
  });
}

function addTitle(slide, titleValue, subtitle) {
  text(slide, {
    name: "slide-title",
    value: titleValue,
    left: FRAME.left,
    top: 75,
    width: 1096,
    height: 62,
    size: 48,
    face: FONT_DISPLAY,
    color: C.ink,
    bold: true,
    lineSpacing: 0.98,
  });
  if (subtitle) {
    text(slide, {
      name: "slide-subtitle",
      value: subtitle,
      left: FRAME.left,
      top: 145,
      width: 980,
      height: 34,
      size: 23,
      color: C.muted,
      lineSpacing: 1.05,
    });
  }
}

async function addImage(slide, assetPath, alt, { left, top, width, height }) {
  const image = slide.images.add({
    blob: await imageBytes(assetPath),
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left, top, width, height },
  });
  return image;
}

function bulletLines(slide, items, { left, top, width, lineHeight = 58, size = 24 }) {
  items.forEach((item, index) => {
    const y = top + index * lineHeight;
    box(slide, { name: `bullet-dot-${index}`, left, top: y + 10, width: 8, height: 8, fill: index === 0 ? C.teal : C.gold });
    text(slide, {
      name: `bullet-${index}`,
      value: item,
      left: left + 22,
      top: y,
      width: width - 22,
      height: lineHeight - 2,
      size,
      color: C.ink,
      lineSpacing: 1.08,
    });
  });
}

function callout(slide, { label, value, left, top, width, accent = C.teal, surface = C.white }) {
  box(slide, { name: `callout-${label}`, left, top, width, height: 110, fill: surface, line: C.line, radius: 8 });
  rule(slide, left, top, 7, accent, 110);
  text(slide, { name: `${label}-value`, value, left: left + 26, top: top + 18, width: width - 40, height: 38, size: 32, face: FONT_DISPLAY, bold: true, color: accent });
  text(slide, { name: `${label}-label`, value: label, left: left + 26, top: top + 66, width: width - 40, height: 24, size: 18, color: C.muted, bold: true });
}

function phaseRow(slide, entries, left, top, width) {
  const column = width / entries.length;
  entries.forEach((entry, index) => {
    const x = left + index * column;
    rule(slide, x, top, column - 18, entry.color, 4);
    text(slide, { name: `phase-code-${index}`, value: entry.code, left: x, top: top + 18, width: column - 18, height: 32, size: 25, bold: true, color: entry.color });
    text(slide, { name: `phase-state-${index}`, value: entry.state, left: x, top: top + 54, width: column - 18, height: 38, size: 23, face: FONT_DISPLAY, bold: true, color: C.ink });
    text(slide, { name: `phase-note-${index}`, value: entry.note, left: x, top: top + 94, width: column - 18, height: 50, size: 18, color: C.muted, lineSpacing: 1.05 });
  });
}

function tableRow(slide, cells, top, options = {}) {
  const { left = FRAME.left, widths, height = 52, header = false, alternate = false } = options;
  let x = left;
  cells.forEach((cell, index) => {
    const width = widths[index];
    box(slide, { name: `table-cell-${top}-${index}`, left: x, top, width, height, fill: header ? C.teal : alternate ? "#F0F5F3" : C.white, line: C.line });
    text(slide, {
      name: `table-text-${top}-${index}`,
      value: cell,
      left: x + 12,
      top: top + 10,
      width: width - 24,
      height: height - 16,
      size: header ? 18 : 20,
      color: header ? C.white : C.ink,
      bold: header || index === 0,
      valign: "middle",
      lineSpacing: 1,
    });
    x += width;
  });
}

function statusStripe(slide, left, top, width, label, color, detail) {
  rule(slide, left, top, width, color, 5);
  text(slide, { name: `${label}-label`, value: label, left, top: top + 18, width, height: 28, size: 23, face: FONT_DISPLAY, bold: true, color });
  text(slide, { name: `${label}-detail`, value: detail, left, top: top + 54, width, height: 48, size: 21, color: C.ink, lineSpacing: 1.03 });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const assetsDir = required(args, "assets");
  const output = required(args, "output");
  const qaDir = required(args, "qa");
  const total = 18;

  const asset = (name) => path.join(assetsDir, name);
  const deck = Presentation.create({ slideSize: PAGE });
  deck.theme.colorScheme = {
    name: "ArmIndex Studio Editorial",
    themeColors: {
      accent1: C.teal, accent2: C.gold, accent3: C.coral, accent4: "#3C6E71", accent5: "#6B4E71", accent6: "#4C7A64",
      bg1: C.paper, bg2: C.white, tx1: C.ink, tx2: C.muted, dk1: C.ink, dk2: "#23313A", lt1: C.white, lt2: C.line,
      hlink: C.teal, folHlink: C.coral,
    },
  };

  // 1. Title
  {
    const slide = deck.slides.add();
    slide.background.fill = "bg1";
    text(slide, { name: "cover-kicker", value: "ADVISOR UPDATE | 18 AUGUST 2026", left: 72, top: 64, width: 500, height: 22, size: 15, color: C.teal, bold: true });
    text(slide, { name: "cover-title", value: "ArmIndex", left: 72, top: 142, width: 570, height: 88, size: 76, face: FONT_DISPLAY, bold: true, color: C.ink, lineSpacing: 0.94 });
    text(slide, { name: "cover-subtitle", value: "Retriever-conditioned representation search for cross-domain patent retrieval.", left: 72, top: 252, width: 590, height: 86, size: 30, color: C.muted, lineSpacing: 1.12 });
    rule(slide, 72, 366, 190, C.teal, 5);
    text(slide, { name: "cover-claim", value: "A controlled sequence: foundation -> common screen -> per-arm search -> transfer and harness design.", left: 72, top: 392, width: 580, height: 58, size: 23, color: C.ink, lineSpacing: 1.1 });
    phaseRow(slide, [
      { code: "A0", state: "Complete", note: "Reproducibility foundation", color: C.teal },
      { code: "A1", state: "25 / 25", note: "Measured REP-DEV screen", color: C.gold },
      { code: "A2", state: "Closed", note: "44 measured; 8 dormant", color: C.coral },
    ], 72, 500, 590);
    await addImage(slide, asset("02_retrieval_system_stack.png"), "Retrieval system stack schematic", { left: 704, top: 94, width: 500, height: 492 });
    text(slide, { name: "cover-boundary", value: "A2 has receipt-bound aggregate development evidence; A3 awaits a hash-bound Train-250 package.", left: 704, top: 602, width: 500, height: 46, size: 18, color: C.muted, lineSpacing: 1.04 });
    addNotes(slide, "Open with the research question and evidence boundary. A2 is closed with exact aggregate accounting, but its results remain development evidence rather than Selection or Final confirmation.", ["[P1] ArmIndex Research Plan V02", "[P2] Current campaign plan", "[P11] A2 Goal 004", "[P17] A2 closeout projection"]);
  }

  // 2. DAPFAM
  {
    const slide = deck.slides.add();
    addChrome(slide, "Context | DAPFAM", 2, total);
    addTitle(slide, "A patent family is the retrieval unit", "A family carries heterogeneous technical and legal text across its ordered fields.");
    await addImage(slide, asset("01_dapfam_family_record_anatomy.png"), "Aggregate-safe DAPFAM family record anatomy", { left: 72, top: 212, width: 624, height: 365 });
    bulletLines(slide, [
      "45,336 target families; 1,247 query families; 49,869 evaluation rows.",
      "IN shares at least one IPC3; OUT shares none.",
      "Citation relevance is an examiner proxy, not a legal conclusion.",
    ], { left: 750, top: 230, width: 450, lineHeight: 94, size: 23 });
    text(slide, { name: "safe-data-note", value: "Raw patent text, IDs, qrels, rankings, and per-query outcomes remain Owner-local.", left: 750, top: 540, width: 430, height: 50, size: 19, color: C.coral, bold: true, lineSpacing: 1.05 });
    addNotes(slide, "Explain why one isolated chunk is inadequate: patent-family retrieval aggregates several fields and publications. The figure deliberately shows the schema, not a raw protected record.", ["[P3] DAPFAM source contract", "[R1] DAPFAM dataset paper"]);
  }

  // 3. GEPA
  {
    const slide = deck.slides.add();
    addChrome(slide, "Methodological lineage | GEPA", 3, total);
    addTitle(slide, "GEPA motivates bounded program search", "The target changes: executable document representations, not free-form answer prompts.");
    await addImage(slide, asset("armindex-research-program.png"), "ArmIndex research program schematic", { left: 660, top: 222, width: 544, height: 306 });
    statusStripe(slide, 72, 220, 520, "GEPA lineage", C.teal, "Reflective, evidence-driven optimization within a constrained text space.");
    statusStripe(slide, 72, 358, 520, "ArmIndex adaptation", C.gold, "A schema-valid representation program is frozen before deterministic retrieval.");
    statusStripe(slide, 72, 496, 520, "Scientific boundary", C.coral, "The proposer and reviewer do not receive protected evaluation signal or results.");
    addNotes(slide, "GEPA is methodological lineage, not a reproduced result. A2 uses Official Codex only before measurement to propose/review bounded, falsifiable programs; production retrieval stays deterministic and hash-bound.", ["[R2] GEPA paper", "[P14] A2 Official Codex bridge", "[P1] ArmIndex Research Plan V02"]);
  }

  // 4. Program overview
  {
    const slide = deck.slides.add();
    addChrome(slide, "Research program", 4, total);
    addTitle(slide, "ArmIndex separates four scientific questions", "The phases intentionally turn one broad idea into testable claims.");
    await addImage(slide, asset("07_a3_transfer_complementarity_harnessopt.png"), "A3 transfer complementarity and HarnessOpt schematic", { left: 650, top: 220, width: 554, height: 312 });
    const programItems = [
      ["1", "Search", "Which program fits each frozen arm?"],
      ["2", "Transfer", "Can one arm's winner help another?"],
      ["3", "Coverage", "Do equal-depth unions recover more families?"],
      ["4", "Harness", "Does quality justify cost and latency?"],
    ];
    programItems.forEach(([num, label, detail], index) => {
      const y = 206 + index * 94;
      text(slide, { name: `program-num-${index}`, value: num, left: 72, top: y, width: 42, height: 38, size: 31, face: FONT_DISPLAY, bold: true, color: index < 2 ? C.teal : C.gold, align: "center" });
      text(slide, { name: `program-label-${index}`, value: label, left: 136, top: y, width: 150, height: 32, size: 24, bold: true, color: C.ink });
      text(slide, { name: `program-detail-${index}`, value: detail, left: 136, top: y + 34, width: 435, height: 50, size: 22, color: C.muted, lineSpacing: 1.03 });
    });
    addNotes(slide, "Use this as the talk's roadmap. Each phase supports a distinct inference and controls what later phases may adapt on.", ["[P1] ArmIndex Research Plan V02", "[P13] A3 Extended Goal 003"]);
  }

  // 5. Retrieval foundations
  {
    const slide = deck.slides.add();
    addChrome(slide, "Retrieval foundations", 5, total);
    addTitle(slide, "Retrieval quality is a full-system property", "Representation affects what is indexed, aggregated, ranked, and ultimately evaluated.");
    await addImage(slide, asset("patent-retrieval-pipeline.png"), "Patent retrieval pipeline schematic", { left: 72, top: 222, width: 630, height: 354 });
    const system = [
      ["Chunking / unitization", "Family, claim, fixed passage, or field view."],
      ["Embedding / indexing", "Frozen templates, pooling, and similarity."],
      ["Aggregation", "MaxP or multiview RRF to one family ranking."],
      ["Evaluation", "OUT Recall@100; retain quality, latency, and cost."],
    ];
    system.forEach(([label, detail], index) => {
      const y = 218 + index * 96;
      rule(slide, 770, y, 410, index === 3 ? C.gold : C.teal, 4);
      text(slide, { name: `system-label-${index}`, value: label, left: 770, top: y + 14, width: 410, height: 28, size: 23, face: FONT_DISPLAY, bold: true, color: C.ink });
      text(slide, { name: `system-detail-${index}`, value: detail, left: 770, top: y + 48, width: 410, height: 44, size: 21, color: C.muted, lineSpacing: 1.04 });
    });
    addNotes(slide, "This slide establishes why chunking is part of the scientific treatment rather than preprocessing. Keep the causal claim modest: ArmIndex measures associations under frozen execution, not a universal mechanism.", ["[P4] Deterministic common-program compiler", "[R1] DAPFAM dataset paper"]);
  }

  // 6. A0 split
  {
    const slide = deck.slides.add();
    addChrome(slide, "A0 | Scientific control", 6, total);
    addTitle(slide, "A0 separates evidence roles", "Development can adapt; later evidence remains reserved for later decisions.");
    await addImage(slide, asset("03_a0_split_and_leakage_control.png"), "A0 protected split and leakage control schematic", { left: 72, top: 210, width: 630, height: 360 });
    callout(slide, { label: "REP-DEV", value: "150", left: 758, top: 230, width: 190, accent: C.teal, surface: C.white });
    callout(slide, { label: "HARNESS-DEV", value: "100", left: 982, top: 230, width: 222, accent: C.gold, surface: C.white });
    text(slide, { name: "a0-policy", value: "Selection-125 is an atomic finalist exposure. Final-872 is the sole confirmation set and remains closed.", left: 758, top: 392, width: 430, height: 78, size: 23, face: FONT_DISPLAY, bold: true, color: C.ink, lineSpacing: 1.06 });
    text(slide, { name: "a0-protect", value: "The protocol releases only aggregate-safe counts and hashes; protected membership and qrels never leave Owner-local storage.", left: 758, top: 502, width: 430, height: 64, size: 20, color: C.muted, lineSpacing: 1.06 });
    addNotes(slide, "The Train-250 split uses seed 42 and protected deterministic membership. Explain the role separation before showing any A1 quality result.", ["[P5] REP/HARNESS split decision", "[P6] A1 publication-impact preregistration"]);
  }

  // 7. A0 delivery
  {
    const slide = deck.slides.add();
    addChrome(slide, "A0 | Foundation", 7, total);
    addTitle(slide, "A0 delivered infrastructure, not a score", "The first phase makes later evidence reproducible, auditable, and protected.");
    await addImage(slide, asset("dapfam-protocol.png"), "DAPFAM protocol and safe evidence schematic", { left: 684, top: 226, width: 520, height: 293 });
    const a0Items = [
      "Canonical controls, schemas, five-arm registry, source locks, and safe evidence paths.",
      "CPU adapter and contract fixtures validated before measured retrieval.",
      "No measured retrieval run, GPU scientific run, protected payload, Selection access, or Final access in A0.",
    ];
    bulletLines(slide, a0Items, { left: 72, top: 224, width: 610, lineHeight: 105, size: 24 });
    text(slide, { name: "a0-contribution", value: "A0 establishes a trustworthy substrate; it makes no retrieval-quality claim.", left: 72, top: 562, width: 610, height: 35, size: 21, color: C.coral, bold: true });
    addNotes(slide, "Make the absence of an A0 quality score explicit. The foundation is evidence infrastructure, not a performance claim.", ["[P7] A0-A2 advisor progress report"]);
  }

  // 8. A1 method
  {
    const slide = deck.slides.add();
    addChrome(slide, "A1 | Common screening", 8, total);
    addTitle(slide, "A1 is a controlled 5 x 5 screen", "Five common representations are measured against five frozen retrieval arms.");
    await addImage(slide, asset("04_a1_representation_programs.png"), "Five A1 representation programs", { left: 72, top: 220, width: 595, height: 354 });
    text(slide, { name: "a1-method-title", value: "The comparison changes one factor", left: 738, top: 226, width: 410, height: 35, size: 27, face: FONT_DISPLAY, bold: true, color: C.ink });
    bulletLines(slide, [
      "P00 full TAC document",
      "P01 title + abstract",
      "P02 first independent claim",
      "P03 fixed passages",
      "P04 field-specific multiview",
    ], { left: 738, top: 282, width: 420, lineHeight: 52, size: 21 });
    text(slide, { name: "a1-complete", value: "25 / 25 valid logical cells on REP-DEV | USD 11.161632", left: 738, top: 564, width: 430, height: 32, size: 20, color: C.gold, bold: true });
    addNotes(slide, "A1 is a common screen, not a final model-selection result. The only changing treatment is the deterministic representation program; evaluator and role remain fixed.", ["[P4] Deterministic common-program compiler", "[P8] A1 validated aggregate evidence"]);
  }

  // 9. Models
  {
    const slide = deck.slides.add();
    addChrome(slide, "A1 | Frozen retrievers", 9, total);
    addTitle(slide, "Five diverse arms expose the interaction", "The arms differ in lexical/dense behavior, domain training, context envelope, and template semantics.");
    const widths = [196, 342, 226, 224, 148];
    tableRow(slide, ["Arm", "Frozen source", "Retrieval role", "Envelope", "License"], 210, { widths, height: 46, header: true });
    const rows = [
      ["ARM-01", "bm25s==0.3.10", "Lexical CPU anchor", "k1=1.2; b=0.75", "MIT"],
      ["ARM-02", "BAAI/bge-m3", "Generic dense", "1,024d; 8,192 tokens", "MIT"],
      ["ARM-03", "datalyes/patembed-large", "Patent-domain dense", "1,024d; 512 tokens", "CC-BY-NC-SA"],
      ["ARM-04", "Snowflake Arctic Embed M v2.0", "Long-context dense", "768d; 8,192 tokens", "Apache-2.0"],
      ["ARM-05", "Qwen3-Embedding-0.6B", "Instruction-aware dense", "1,024d; 32,768 tokens", "Apache-2.0"],
    ];
    rows.forEach((row, index) => tableRow(slide, row, 256 + index * 56, { widths, height: 56, alternate: index % 2 === 1 }));
    text(slide, { name: "model-note", value: "Exact public revisions, pooling, query/document templates, and non-commercial qualification for ARM-03 are frozen in the speaker notes and backup material.", left: 72, top: 564, width: 1040, height: 46, size: 20, color: C.muted, lineSpacing: 1.05 });
    addNotes(slide, "Each arm is bound to a specific model revision and adapter template. ARM-01 has no embedding prompt. ARM-03 remains research/non-commercial. The full exact templates are documented in Appendix B of the material.", ["[P9] A1 model source locks", "[P10] Frozen dense adapter contract", "[R4]-[R7] Official model cards"]);
  }

  // 10. A1 quality
  {
    const slide = deck.slides.add();
    addChrome(slide, "A1 | REP-DEV result", 10, total);
    addTitle(slide, "A1 reveals a broad quality range", "The representation surface differs across frozen retriever arms.");
    await addImage(slide, asset("05_a1_mean_out_recall.png"), "A1 mean OUT Recall at 100 across arms", { left: 72, top: 210, width: 680, height: 330 });
    callout(slide, { label: "Highest common cell", value: "P03", left: 816, top: 224, width: 330, accent: C.teal, surface: C.white });
    text(slide, { name: "a1-quality-copy", value: "Fixed passages obtain the highest individual Recall@100 cell in all five arms.", left: 816, top: 374, width: 350, height: 62, size: 24, face: FONT_DISPLAY, bold: true, color: C.ink, lineSpacing: 1.06 });
    text(slide, { name: "a1-promotion", value: "ARM-03, ARM-04, and ARM-05 pass the frozen promotion rule; ARM-01 and ARM-02 remain diagnostic/non-advancing in A2.", left: 816, top: 474, width: 350, height: 90, size: 20, color: C.muted, lineSpacing: 1.06 });
    text(slide, { name: "a1-boundary", value: "REP-DEV descriptive evidence only; not Selection or Final confirmation.", left: 72, top: 576, width: 680, height: 28, size: 19, color: C.coral, bold: true });
    addNotes(slide, "Read the arm means as a quality spread, not a final model selection. The arm-level numbers are 0.191, 0.270, 0.413, 0.341, and 0.364 mean OUT Recall@100 for BM25, BGE-M3, PatEmbed, Arctic, and Qwen3 respectively.", ["[P8] A1 cell EDA CSV and validated figures"]);
  }

  // 11. A1 operations
  {
    const slide = deck.slides.add();
    addChrome(slide, "A1 | Operational evidence", 11, total);
    addTitle(slide, "Quality gains bring physical work", "The quality-latency-cost frontier is a result, not an afterthought.");
    await addImage(slide, asset("a12-v16-20260811-r15.efficiency-cell-eda.v16.png"), "A1 efficiency cell EDA", { left: 72, top: 218, width: 1136, height: 387 });
    text(slide, { name: "a1-operations-caption", value: "The full receipt-bound frontier retains quality, p95 latency, wall time, VRAM, RAM, index size, and cost together.", left: 72, top: 620, width: 1136, height: 26, size: 20, color: C.muted, lineSpacing: 1.04 });
    addNotes(slide, "Use the EDA to distinguish the common-screen pattern from deployment policy. No conclusion is drawn from Recall alone; later phases preserve p95 latency, throughput, cost, RAM, VRAM, and index-size receipts.", ["[P8] A1 efficiency EDA", "[P13] A3 Extended Goal 003"]);
  }

  // 12. A2 flow
  {
    const slide = deck.slides.add();
    addChrome(slide, "A2 | Per-arm AutoIndex", 12, total);
    addTitle(slide, "A2 evaluates a frozen candidate universe", "Candidate generation is pre-measurement; evaluation remains deterministic and checkpointed.");
    await addImage(slide, asset("06_a2_execution_and_reserve_flow.png"), "A2 execution and reserve admission flow", { left: 72, top: 210, width: 658, height: 360 });
    callout(slide, { label: "Frozen candidates", value: "52", left: 798, top: 228, width: 330, accent: C.teal, surface: C.white });
    text(slide, { name: "a2-count", value: "40 matched + 12 conditional reserve candidates", left: 798, top: 360, width: 370, height: 52, size: 22, color: C.ink, lineSpacing: 1.05 });
    bulletLines(slide, [
      "ARM-01 is CPU; ARM-02-05 use separate GPUs.",
      "Each candidate has a durable checkpoint and heartbeat.",
      "Reserves need fresh barrier, budget, and TTL admission.",
    ], { left: 798, top: 446, width: 394, lineHeight: 60, size: 21 });
    addNotes(slide, "Define dormant carefully. A dormant reserve candidate is not zero, null, failure, or equal to the baseline. It was not evaluated because its pre-registered admission predicate did not trigger.", ["[P11] A2 Goal 004", "[P12] A2 execution runbook", "[P14] A2 Official Codex bridge"]);
  }

  // 13. A2 measured closeout
  {
    const slide = deck.slides.add();
    addChrome(slide, "A2 | Measured closeout", 13, total);
    addTitle(slide, "A2 closes with bounded primary inputs", "Exact accounting, safe return, and an independent audit support aggregate-only interpretation.");
    await addImage(slide, asset("a2-goal004-outcomes.png"), "A2 receipt-bound aggregate outcomes by arm", { left: 72, top: 218, width: 658, height: 360 });
    statusStripe(slide, 764, 224, 414, "ARM-03", C.teal, "Recall@100 0.4230; numerical tie to A1 at presentation precision.");
    statusStripe(slide, 764, 356, 414, "ARM-04", C.gold, "Recall@100 0.3587; strict +0.0060 improvement over A1.");
    statusStripe(slide, 764, 488, 414, "ARM-05", C.coral, "Recall@100 0.3737; no strict A1 improvement, retained for transfer.");
    addNotes(slide, "A2 passed execution closeout and result-integrity audit: 52 equals 44 measured plus 8 dormant, with zero failures, safe return, and worker reaping. ARM-01 and ARM-02 are three-way diagnostic ties with no winner and are excluded. ARM-03, ARM-04, and ARM-05 are the three approved A3 transfer inputs. No Selection or Final claim is supported.", ["[P11] A2 Goal 004", "[P17] A2 closeout projection", "[P18] A2 execution closeout and integrity audit"]);
  }

  // 14. A3
  {
    const slide = deck.slides.add();
    addChrome(slide, "A3 Extended | Pending input package", 14, total);
    addTitle(slide, "A3 needs a fresh hash-bound Train-250 package", "ARM-03, ARM-04, and ARM-05 are prepared; admission and spend remain closed.");
    await addImage(slide, asset("07_a3_transfer_complementarity_harnessopt.png"), "Three-primary A3 transfer, complementarity, and HarnessOpt design", { left: 72, top: 224, width: 560, height: 303 });
    const a3 = [
      ["Transfer", "3 self-reuses + up to 6 compatible cross-arm transfers."],
      ["Complementarity", "Equal-depth unions first; commercial-only union is ARM-04 + ARM-05."],
      ["HarnessOpt", "At most three complete batches; quality, cost/latency, routing, and diversity roles."],
      ["Admission", "Hash-bound Train-250, fresh provider receipt, USD 35 A3 cap, USD 180 campaign ceiling."],
    ];
    a3.forEach(([label, detail], index) => {
      const y = 180 + index * 110;
      rule(slide, 656, y, 90, index === 3 ? C.coral : C.teal, 4);
      text(slide, { name: `a3-label-${index}`, value: label, left: 656, top: y + 12, width: 250, height: 48, size: 23, face: FONT_DISPLAY, bold: true, color: C.ink });
      text(slide, { name: `a3-detail-${index}`, value: detail, left: 656, top: y + 64, width: 520, height: 46, size: 19, color: C.muted, lineSpacing: 1.04 });
    });
    addNotes(slide, "A3 is prepared but cannot launch. It requires a fresh Owner-authorized hash-bound Train-250 query/corpus/evaluator package, then a fresh provider admission. The three-primary route excludes ARM-01 and ARM-02 permanently from A3 optimization.", ["[P13] A3 Extended Goal 003", "[P5] REP/HARNESS split decision", "[P17] A2 closeout projection"]);
  }

  // 15. Close
  {
    const slide = deck.slides.add();
    addChrome(slide, "Takeaway", 15, total);
    addTitle(slide, "ArmIndex is an auditable interaction test", "The contribution is a defensible research sequence, not a one-off model win.");
    const takeaway = [
      ["A0", "made the scientific sequence controlled and reproducible.", C.teal],
      ["A1", "showed a representation-by-retriever quality and cost surface.", C.gold],
      ["A2", "closed with three transfer inputs and bounded negative evidence.", C.coral],
      ["A3", "will test the three-primary transfer and operational frontier.", C.teal],
    ];
    takeaway.forEach(([code, detail, color], index) => {
      const x = 72 + index * 284;
      rule(slide, x, 232, 250, color, 6);
      text(slide, { name: `takeaway-code-${index}`, value: code, left: x, top: 260, width: 250, height: 46, size: 36, face: FONT_DISPLAY, bold: true, color });
      text(slide, { name: `takeaway-detail-${index}`, value: detail, left: x, top: 326, width: 250, height: 94, size: 21, color: C.ink, lineSpacing: 1.07 });
    });
    text(slide, { name: "next-update", value: "The next meaningful update is a hash-bound Train-250 package and fresh A3 admission, not reuse of an idle instance.", left: 72, top: 520, width: 1020, height: 60, size: 27, face: FONT_DISPLAY, bold: true, color: C.ink, lineSpacing: 1.05 });
    addNotes(slide, "Close on the evidence sequence. The advisor discussion is whether the A2 evidence justifies the bounded three-primary A3 design and whether its required Train-250 package can be bound without weakening the protocol.", ["[P1] ArmIndex Research Plan V02", "[P11] A2 Goal 004", "[P13] A3 Extended Goal 003"]);
  }

  // 16. Appendix split
  {
    const slide = deck.slides.add();
    addChrome(slide, "Appendix A | Evidence roles", 16, total);
    addTitle(slide, "Appendix: the split protects the sequence", "The allocation is a protocol decision that limits what can adapt at each stage.");
    await addImage(slide, asset("a1.2-dense-overflow-eda-v1.png"), "Dense overflow windowing diagnostic", { left: 72, top: 212, width: 666, height: 346 });
    bulletLines(slide, [
      "REP-DEV is used for A1 screening and A2 representation search.",
      "HARNESS-DEV supports A3 transfer, complementarity, and bounded harness optimization after representation freeze.",
      "Selection and Final remain protected from adaptive development use.",
    ], { left: 822, top: 228, width: 358, lineHeight: 95, size: 21 });
    addNotes(slide, "This backup slide documents the rationale for the staged split and shows a safe aggregate windowing diagnostic. It does not open protected membership or qrels.", ["[P5] REP/HARNESS split decision", "[P6] A1 preregistration", "[P8] Dense-overflow EDA"]);
  }

  // 17. Appendix model contracts
  {
    const slide = deck.slides.add();
    addChrome(slide, "Appendix B | Model contracts", 17, total);
    addTitle(slide, "Appendix: frozen model contracts", "Templates, pooling, and revisions are part of each measured retrieval identity.");
    const widths = [142, 344, 342, 308];
    tableRow(slide, ["Arm", "Query template", "Document / pooling", "Revision"], 206, { widths, height: 46, header: true });
    const contracts = [
      ["ARM-01", "No embedding prompt", "BM25 lexical scoring", "bm25s==0.3.10"],
      ["ARM-02", "{query}", "{document}; official dense parity", "5617a9f..."],
      ["ARM-03", "encode query for different document retrieval: {query}", "document prefix; mean non-padding", "2d5c0f9..."],
      ["ARM-04", "query: {query}", "{document}; CLS / first token", "95c2741..."],
      ["ARM-05", "Instruct: Retrieve patent families ... Query:{query}", "{document}; last token / left padding", "97b0c61..."],
    ];
    contracts.forEach((row, index) => tableRow(slide, row, 252 + index * 62, { widths, height: 62, alternate: index % 2 === 1 }));
    text(slide, { name: "contract-note", value: "Full immutable template text, public hashes, dimensions, token envelopes, licenses, and pooling rules are retained in the source locks and the talk material.", left: 72, top: 578, width: 1040, height: 32, size: 19, color: C.muted });
    addNotes(slide, "Read exact binding from the material Appendix A. ARM-02 revision 5617a9f61b028005a4858fdac845db406aefb181; ARM-03 2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad; ARM-04 95c2741480856aa9666782eb4afe11959938017f; ARM-05 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3.", ["[P9] A1 model source locks", "[P10] Frozen dense adapter contract", "[R4]-[R7] Official model cards"]);
  }

  // 18. Appendix prompts
  {
    const slide = deck.slides.add();
    addChrome(slide, "Appendix C | Prompt governance", 18, total);
    addTitle(slide, "Appendix: audited prompt governance", "Official Codex proposes and reviews only pre-measurement, aggregate-safe candidate programs.");
    box(slide, { name: "proposer-surface", left: 72, top: 218, width: 520, height: 310, fill: C.white, line: C.line, radius: 8 });
    rule(slide, 72, 218, 520, C.teal, 5);
    text(slide, { name: "proposer-title", value: "Proposer template", left: 100, top: 248, width: 420, height: 34, size: 29, face: FONT_DISPLAY, bold: true, color: C.ink });
    bulletLines(slide, [
      "Returns schema-constrained JSON for exactly four requested slots.",
      "Uses only frozen aggregate-safe operation payload.",
      "States a falsifiable intervention, comparator, expected direction, and failure condition.",
      "Preserves accepted candidates byte-for-byte on revision rounds.",
    ], { left: 104, top: 308, width: 438, lineHeight: 51, size: 18 });
    box(slide, { name: "reviewer-surface", left: 688, top: 218, width: 520, height: 310, fill: C.white, line: C.line, radius: 8 });
    rule(slide, 688, 218, 520, C.gold, 5);
    text(slide, { name: "reviewer-title", value: "Independent reviewer template", left: 716, top: 248, width: 440, height: 34, size: 29, face: FONT_DISPLAY, bold: true, color: C.ink });
    bulletLines(slide, [
      "Checks determinism, role fit, duplication, safety, and interpretability.",
      "Cannot change evaluator, metrics, promotion rule, model weights, or protected split.",
      "No qrels, query IDs, memberships, rankings, protected text, or measured results.",
      "Accepts only candidates satisfying every frozen check.",
    ], { left: 720, top: 308, width: 438, lineHeight: 51, size: 18 });
    text(slide, { name: "prompt-binding", value: "Model binding: gpt-5.6-sol, high reasoning effort, before A2 measurement. Full exact prompt templates are retained in the speaker notes and material Appendix D.", left: 72, top: 570, width: 1100, height: 38, size: 19, color: C.coral, bold: true, lineSpacing: 1.04 });
    addNotes(slide, "Full exact proposer template:\n\nYou are the Official Codex representation proposer for a pre-measurement, five-arm patent-retrieval study. Return only JSON matching the supplied output schema.\n\nUse only the frozen aggregate-safe payload below. Propose exactly the four requested candidate slots. Preserve every candidate ID and role exactly. Make each hypothesis falsifiable, retriever-conditioned, compatible with the listed source fields, and distinct from the other candidates in the batch. Do not use or request qrels, query IDs, membership, rankings, per-query outcomes, protected text, credentials, provider payloads, or measured results. Do not claim that an unmeasured candidate improves retrieval. Do not expose hidden reasoning.\n\nFor program fields, use only the allowed source fields and ensure field_order contains exactly the same fields once. Keep logical passage sizes conservative for the declared arm limit. ARM-01 and ARM-02 candidates are diagnostic only when the payload says advancement_eligible=false.\n\nEvery hypothesis must identify one deterministic representation intervention, the frozen within-arm comparator, the expected direction that can later be falsified, and a concrete failure condition without claiming improvement. Avoid learned, adaptive, data-dependent, ranking-dependent, or unspecified processing. Keep each candidate attributable to its declared axis and explain it in language suitable for a journal ablation. For conditional reserve slots, state that the candidate remains dormant unless the frozen activation predicate is satisfied. Apply every reviewer_required_changes item to its named candidate while keeping the other slots independently valid. On revision rounds, accepted_candidate_ids are immutable: copy those candidates from previous_candidates byte-for-byte, including their hypothesis, program, expected_effect, and failure_risk. Revise only candidate IDs that are not in accepted_candidate_ids. Return all four slots in the canonical order.\n\nOperation payload:\n\n{{OPERATION_PAYLOAD_JSON}}\n\nFull exact reviewer template:\n\nYou are the independent Official Codex reviewer for a frozen pre-measurement representation-candidate batch. Return only JSON matching the supplied output schema.\n\nReview only the frozen aggregate-safe context and candidate payload below. You have no proposer transcript and no measured outcomes. Preserve every candidate ID. Check falsifiability, role fit, duplication, protected-boundary safety, arm compatibility, deterministic interpretability, and publication interpretability. Accept only candidates that satisfy every check. Required changes must be specific and must not alter the frozen evaluator, metrics, A1 promotion, model weights, protected split, or diagnostic non-advancement. Do not expose hidden reasoning.\n\npreviously_accepted_candidate_ids were accepted in an earlier independent review and are required to be byte-identical in this round. Recheck them, but do not request stylistic changes or reinterpret their scientific semantics. Reject a previously accepted candidate only for a concrete newly observed safety, determinism, duplication, or contract defect.\n\nOperation payload:\n\n{{OPERATION_PAYLOAD_JSON}}", ["[P14] A2 Official Codex bridge", "[P15] A2 representation proposer prompt", "[P16] A2 representation reviewer prompt"]);
  }

  await fs.mkdir(qaDir, { recursive: true });
  const sourceNotes = [
    "ArmIndex Advisor Talk PPTX source notes",
    "Primary narrative: docs/presentation/material/ARMINDEX_ADVISOR_TALK_MATERIAL.md",
    "Figures F01-F07 and supplementary aggregate-safe figures are embedded as rasterized local assets.",
    "A1 values are validated REP-DEV aggregates. A2 is receipt-bound aggregate development evidence, with no Selection or Final claim.",
  ].join("\n");
  await fs.writeFile(path.join(qaDir, "source-notes.txt"), `${sourceNotes}\n`, "utf8");

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(qaDir, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await (await slide.export({ format: "layout" })).text());
  }
  const inspection = await deck.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 200000 });
  await fs.writeFile(path.join(qaDir, "deck.inspect.ndjson"), inspection.ndjson, "utf8");
  await writeBlob(path.join(qaDir, "deck-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  await (await PresentationFile.exportPptx(deck)).save(output);
  console.log(JSON.stringify({ output, qaDir, slides: deck.slides.items.length }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
