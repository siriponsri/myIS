import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const progressRoot = process.env.PROGRESS_ROOT
  ? path.resolve(process.env.PROGRESS_ROOT)
  : path.resolve(process.cwd(), "docs", "presentation", "progress");
const repoRoot = path.resolve(progressRoot, "..", "..", "..");
const outputPath = path.join(progressRoot, "ArmIndex_Progress_A0_A3_2026-08-18.pptx");
const inspectPath = `${outputPath}.inspect.ndjson`;
const renderRoot = path.join(progressRoot, "render");

const colors = {
  paper: "F8FAFC",
  ink: "14213D",
  muted: "52616B",
  line: "CBD5E1",
  blue: "0F6CBD",
  teal: "007F80",
  green: "2A6F4E",
  amber: "A15C00",
  paleBlue: "E8F1FA",
  paleTeal: "E7F5F4",
  paleAmber: "FFF4E5",
  white: "FFFFFF",
};

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, position, style = {}, name = "text") {
  const box = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: "Aptos",
    fontSize: 24,
    color: colors.ink,
    verticalAlignment: "top",
    ...style,
  };
  return box;
}

function addRect(slide, position, fill, name = "surface", line = colors.line) {
  return slide.shapes.add({
    geometry: "roundRect",
    name,
    position,
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: "rounded-lg",
  });
}

function addHeader(slide, title, number) {
  addText(slide, "ARMINDEX | ADVISOR PROGRESS UPDATE", { left: 72, top: 36, width: 660, height: 22 }, {
    fontSize: 14,
    bold: true,
    color: colors.blue,
  }, "eyebrow");
  addText(slide, title, { left: 72, top: 72, width: 1050, height: 64 }, {
    fontSize: 40,
    bold: true,
    color: colors.ink,
  }, "title");
  addText(slide, `${number} / 6`, { left: 1136, top: 42, width: 72, height: 20 }, {
    fontSize: 14,
    color: colors.muted,
    alignment: "right",
  }, "slide-number");
}

function addFooter(slide, text) {
  slide.shapes.add({
    geometry: "straightConnector1",
    name: "footer-rule",
    position: { left: 72, top: 656, width: 1136, height: 0 },
    fill: "none",
    line: { style: "solid", fill: colors.line, width: 1 },
  });
  addText(slide, text, { left: 72, top: 668, width: 980, height: 20 }, {
    fontSize: 12,
    color: colors.muted,
  }, "footer");
}

function addNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines.join("\n"));
  slide.speakerNotes.setVisible(true);
}

async function addImage(slide, filePath, alt, position, name) {
  slide.images.add({
    blob: await imageBytes(filePath),
    contentType: "image/png",
    alt,
    fit: "contain",
    position,
    geometry: "rect",
    name,
  });
}

function addPhase(slide, x, label, state, fill) {
  addRect(slide, { left: x, top: 297, width: 230, height: 188 }, colors.white, `phase-${label}`);
  addRect(slide, { left: x + 20, top: 317, width: 64, height: 28 }, fill, `phase-tag-${label}`, fill);
  addText(slide, label, { left: x + 29, top: 322, width: 48, height: 18 }, {
    fontSize: 14,
    bold: true,
    color: colors.white,
    alignment: "center",
  }, `phase-label-${label}`);
  addText(slide, state, { left: x + 20, top: 366, width: 185, height: 44 }, {
    fontSize: 22,
    bold: true,
    color: colors.ink,
  }, `phase-state-${label}`);
}

async function main() {
  await fs.mkdir(progressRoot, { recursive: true });
  await fs.rm(renderRoot, { recursive: true, force: true });
  await fs.mkdir(renderRoot, { recursive: true });

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  const figures = path.join(repoRoot, "docs", "progress_report", "figures");

  // Slide 1: title / current state.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addText(slide, "ARMINDEX", { left: 72, top: 52, width: 260, height: 30 }, {
      fontSize: 18,
      bold: true,
      color: colors.blue,
    }, "eyebrow");
    addText(slide, "Progress Update", { left: 72, top: 170, width: 800, height: 90 }, {
      fontSize: 62,
      bold: true,
      color: colors.ink,
    }, "title");
    addText(slide, "Retriever-specific document representation search for cross-domain patent retrieval", { left: 72, top: 280, width: 830, height: 72 }, {
      fontSize: 28,
      color: colors.muted,
    }, "subtitle");
    addRect(slide, { left: 72, top: 432, width: 910, height: 78 }, colors.paleTeal, "status-surface", colors.paleTeal);
    addText(slide, "A0-A3 complete | Result audit passed | A4 remains gated", { left: 98, top: 457, width: 850, height: 30 }, {
      fontSize: 25,
      bold: true,
      color: colors.green,
    }, "status");
    addText(slide, "19 August 2026", { left: 72, top: 612, width: 350, height: 24 }, {
      fontSize: 16,
      color: colors.muted,
    }, "date");
    addFooter(slide, "Summary advisor update. Selection and final confirmation remain closed.");
    addNotes(slide, [
      "The central question is whether the best deterministic representation of a patent family depends on the retriever.",
      "This update reports completed evidence through A3. The A3 result is aggregate-safe development evidence; it does not open production transfer, Selection, or Final.",
      "[Sources]",
      "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md",
      "docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md",
    ]);
  }

  // Slide 2: research progression.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addHeader(slide, "A0-A3 advances to transfer measurement", 2);
    addText(slide, "Each phase answers a narrower question while keeping retrievers, scoring rules, and data protections controlled.", { left: 72, top: 155, width: 1000, height: 48 }, {
      fontSize: 23,
      color: colors.muted,
    }, "subtitle");
    addPhase(slide, 72, "A0", "Controls", colors.blue);
    addPhase(slide, 336, "A1", "Common comparison", colors.teal);
    addPhase(slide, 600, "A2", "Representation search", colors.green);
    addPhase(slide, 864, "A3", "Transfer study", colors.amber);
    addText(slide, "complete", { left: 92, top: 430, width: 120, height: 25 }, { fontSize: 18, color: colors.green }, "a0-status");
    addText(slide, "complete", { left: 356, top: 430, width: 120, height: 25 }, { fontSize: 18, color: colors.green }, "a1-status");
    addText(slide, "complete", { left: 620, top: 430, width: 120, height: 25 }, { fontSize: 18, color: colors.green }, "a2-status");
    addText(slide, "audit passed", { left: 884, top: 430, width: 210, height: 25 }, { fontSize: 18, color: colors.green }, "a3-status");
    addText(slide, "A4 remains locked until A3 evidence is collected and audited.", { left: 72, top: 548, width: 850, height: 38 }, {
      fontSize: 24,
      bold: true,
      color: colors.ink,
    }, "takeaway");
    addFooter(slide, "Phase roles and A3 scope are set before measurement.");
    addNotes(slide, [
      "A0 establishes reproducibility and data-protection controls. A1 tests the common comparison. A2 conducts constrained representation search for each retriever.",
      "A3 now tests whether selected representations transfer and whether combining retrievers adds useful coverage under operational constraints.",
      "[Sources]",
      "docs/progress_report/update_A0_A1_A2_18AUG2026.md",
      "docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md",
    ]);
  }

  // Slide 3: protocol protection.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addHeader(slide, "A0 separates development from future confirmation", 3);
    addText(slide, "Predefined data roles keep adaptive development away from later confirmation decisions.", { left: 72, top: 155, width: 1000, height: 42 }, {
      fontSize: 23,
      color: colors.muted,
    }, "subtitle");
    addRect(slide, { left: 72, top: 240, width: 365, height: 265 }, colors.white, "method-summary");
    addText(slide, "Why it matters", { left: 98, top: 270, width: 260, height: 28 }, { fontSize: 25, bold: true }, "why-title");
    addText(slide, "- Representation development has a predefined role\n- Harness development is separated\n- Selection and final confirmation remain closed", { left: 98, top: 330, width: 300, height: 132 }, {
      fontSize: 21,
      color: colors.ink,
    }, "why-body");
    await addImage(slide, path.join(figures, "a1-development-role-split.png"), "Diagram showing the predefined roles for representation and harness development", { left: 480, top: 212, width: 690, height: 355 }, "development-role-figure");
    addText(slide, "The figure shows role separation only; it contains no protected membership or relevance labels.", { left: 480, top: 582, width: 690, height: 40 }, {
      fontSize: 16,
      color: colors.muted,
    }, "figure-caption");
    addFooter(slide, "A0 is engineering and reproducibility evidence, not a retrieval-performance result.");
    addNotes(slide, [
      "The study keeps representation development and later harness development separate. Selection and final confirmation have not been opened.",
      "The figure shows role separation only; it exposes no protected membership or relevance labels.",
      "[Sources]",
      "docs/progress_report/update_A0_A1_A2_18AUG2026.md",
      "docs/progress_report/figures/a1-development-role-split.png",
    ]);
  }

  // Slide 4: A1 / A2 completeness.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addHeader(slide, "A1 and A2 establish complete development evidence", 4);
    addText(slide, "A1 maps the common comparison; A2 searches a predefined candidate set for each retriever.", { left: 72, top: 155, width: 1070, height: 42 }, {
      fontSize: 23,
      color: colors.muted,
    }, "subtitle");
    addRect(slide, { left: 72, top: 235, width: 350, height: 300 }, colors.paleBlue, "a1-summary", colors.paleBlue);
    addText(slide, "A1", { left: 102, top: 268, width: 110, height: 42 }, { fontSize: 28, bold: true, color: colors.blue }, "a1-label");
    addText(slide, "5 representations\nx 5 frozen retrievers\n= 25 completed cells", { left: 102, top: 334, width: 265, height: 135 }, {
      fontSize: 26,
      bold: true,
      color: colors.ink,
    }, "a1-value");
    await addImage(slide, path.join(figures, "a2-coverage-recovery.png"), "A2 candidate accounting showing 44 measured and eight dormant candidates", { left: 455, top: 206, width: 710, height: 390 }, "a2-coverage-figure");
    addText(slide, "A2 accounting", { left: 72, top: 558, width: 245, height: 24 }, {
      fontSize: 17,
      bold: true,
      color: colors.blue,
    }, "a2-accounting-label");
    addText(slide, "52 = 44 measured + 8 dormant", { left: 72, top: 586, width: 350, height: 30 }, {
      fontSize: 22,
      bold: true,
      color: colors.ink,
    }, "a2-accounting");
    addText(slide, "Dormant means not admitted for evaluation; it is not failure or zero performance.", { left: 455, top: 608, width: 710, height: 26 }, {
      fontSize: 15,
      color: colors.muted,
      alignment: "center",
    }, "a2-caption");
    addFooter(slide, "A1 and A2 are summary development evidence; they are not Selection or Final confirmation.");
    addNotes(slide, [
      "A1 measured five fixed representations across five predefined retrieval arms. A2 then searched its predefined candidate set independently for each arm.",
      "All 52 authorized candidate slots are accounted for: 44 were measured and eight conditional reserves were dormant. A dormant reserve is not a missing or null result.",
      "[Sources]",
      "docs/progress_report/update_A0_A1_A2_18AUG2026.md",
      "docs/progress_report/figures/a2-coverage-recovery.png",
    ]);
  }

  // Slide 5: A2 decision.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addHeader(slide, "A2 advances three retrievers to A3", 5);
    addText(slide, "The advancement rule retains interpretable ties and no-gain outcomes instead of selecting only positive results.", { left: 72, top: 155, width: 1070, height: 42 }, {
      fontSize: 23,
      color: colors.muted,
    }, "subtitle");
    await addImage(slide, path.join(figures, "a2-per-arm-outcomes.png"), "A2 per-arm outcomes and A3 eligibility", { left: 72, top: 215, width: 720, height: 380 }, "a2-outcomes-figure");
    addRect(slide, { left: 835, top: 227, width: 340, height: 205 }, colors.paleTeal, "primary-arms", colors.paleTeal);
    addText(slide, "Primary A3 inputs", { left: 865, top: 252, width: 260, height: 28 }, { fontSize: 23, bold: true, color: colors.green }, "primary-title");
    addText(slide, "ARM-03  PatEmbed\nARM-04  Arctic Embed\nARM-05  Qwen3 Embedding", { left: 865, top: 304, width: 260, height: 95 }, {
      fontSize: 20,
      bold: true,
      color: colors.ink,
    }, "primary-list");
    addRect(slide, { left: 835, top: 455, width: 340, height: 115 }, colors.paleAmber, "diagnostic-arms", colors.paleAmber);
    addText(slide, "ARM-01 and ARM-02 are retained for interpretation but do not advance.", { left: 865, top: 481, width: 270, height: 56 }, {
      fontSize: 19,
      color: colors.amber,
      bold: true,
    }, "diagnostic-note");
    addFooter(slide, "Only ARM-03, ARM-04, and ARM-05 enter A3 transfer and complementarity measurement.");
    addNotes(slide, [
      "ARM-03, ARM-04, and ARM-05 are the only A3 inputs. ARM-01 and ARM-02 had three-way top ties without a unique winner and remain useful interpretation evidence.",
      "ARM-04 is the strict A2 improvement; ARM-03 is a numerical tie at reported precision; ARM-05 is retained without a strict A2 improvement to avoid selecting only positive outcomes.",
      "[Sources]",
      "docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md",
      "docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv",
      "docs/progress_report/figures/a2-per-arm-outcomes.png",
    ]);
  }

  // Slide 6: A3 audited result and A4 gate.
  {
    const slide = presentation.slides.add();
    slide.background.fill = colors.paper;
    addHeader(slide, "A3 result audit: transfer is adapter-dependent", 6);
    addText(slide, "All 14 Train-250 operations completed; the strongest fixed control is top-two RRF-60.", { left: 72, top: 155, width: 1050, height: 42 }, {
      fontSize: 23,
      color: colors.muted,
    }, "subtitle");
    await addImage(slide, path.join(figures, "a3-transfer-recall-heatmap-20260819.png"), "A3 transfer matrix showing OUT Recall at 100 for three source programs and three target adapters", { left: 72, top: 215, width: 610, height: 355 }, "a3-transfer-figure");
    addRect(slide, { left: 720, top: 215, width: 458, height: 355 }, colors.paleTeal, "a3-results", colors.paleTeal);
    addText(slide, "Audited findings", { left: 750, top: 247, width: 330, height: 30 }, { fontSize: 24, bold: true, color: colors.green }, "results-title");
    addText(slide, "- Best transfer: ARM-05 -> ARM-03, Recall@100 0.419\n- Best fixed control: top-two RRF-60, Recall@100 0.419\n- All-primary union: 0.415 Recall@100\n- HarnessOpt: flat surface, no adaptive gain", { left: 750, top: 307, width: 390, height: 150 }, { fontSize: 19, color: colors.ink }, "results-body");
    addText(slide, "A4 remains locked; Selection and Final remain closed.", { left: 750, top: 500, width: 390, height: 35 }, { fontSize: 19, bold: true, color: colors.blue }, "results-boundary");
    addText(slide, "Claim-limited development evidence: transfer depends on the adapter, and adding every arm is not automatically complementary.", { left: 72, top: 595, width: 1080, height: 38 }, {
      fontSize: 20,
      bold: true,
      color: colors.ink,
    }, "next-step");
    addFooter(slide, "A3 development evidence only. Selection and Final remain closed.");
    addNotes(slide, [
      "All 14 authorized operations completed on Train-250 and passed an independent aggregate-only result-integrity audit.",
      "The transfer heatmap shows adapter-dependent quality. The strongest fixed control is top-two RRF-60; the all-primary union is lower on the development workload.",
      "HarnessOpt compiled three complete batches into one effective action signature, so the valid conclusion is a flat-surface stop rather than an adaptive improvement claim.",
      "A4 readiness is prepared contractually, but Selection and Final remain closed.",
      "[Sources]",
      "docs/progress_report/update_A3_19AUG2026.md",
      "docs/progress_report/figures/a3-transfer-recall-heatmap-20260819.png",
      "docs/progress_report/A3_transfer_matrix_eda_20260819.csv",
    ]);
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    await writeBlob(path.join(renderRoot, `slide-${String(index + 1).padStart(2, "0")}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
  }
  await writeBlob(path.join(renderRoot, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const inspection = await presentation.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 30000 });
  await fs.writeFile(inspectPath, inspection.ndjson, "utf8");
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
