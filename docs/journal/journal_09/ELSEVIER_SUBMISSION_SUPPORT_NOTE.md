# Elsevier submission-support evidence

Date checked: 2026-09-02  
Target package: `docs/journal/journal_09/`  
Target journal: *World Patent Information*

This note records the additional Elsevier Journal Article Publishing Support
Center material supplied for the submission gate. These are generic Elsevier
instructions; the current *World Patent Information* Guide for Authors and the
live Editorial Manager questions take precedence wherever they differ.

## Sources and operational implications

| Support resource | Verified operational point | Package implication |
|---|---|---|
| [Video Guide: New submission experience - An author overview](https://www.elsevier.support/publishing/answer/video-guide-new-submission-experience-an-author-overview) | The current Editorial Manager submission flow is presented as a new author experience. | Perform the final checks in the current submission interface; do not infer required fields from an older workflow. |
| [Author Guide to Editorial Manager](https://www.elsevier.support/publishing/answer/author-guide-to-editorial-manager) | The guide links to preparation, LaTeX, declaration, and submission resources. | Use it as the navigation hub for the live submission workflow. |
| [WPI Editorial Manager](https://www.editorialmanager.com/wpi/) | The public landing page is reachable and identifies *World Patent Information*. Its Instructions for Authors link resolves to the official WPI Guide for Authors URL, which returned HTTP 403 outside an interactive browser. | The journal and submission-system binding is verified; the Owner must still inspect the linked guide and journal-specific upload questions in the live interface. |
| [How do I submit a manuscript in Editorial Manager?](https://www.elsevier.support/publishing/answer/how-do-i-submit-a-manuscript-in-editorial-manager) | The submission article describes the current step-by-step Editorial Manager flow and points authors to the journal's own instructions. | Use the live journal link and current EM sequence at upload; this repository does not attempt to simulate an authenticated submission. |
| [How do I prepare my files for submission in Editorial Manager?](https://www.elsevier.support/publishing/answer/how-do-i-prepare-my-files-for-submission-in-editorial-manager) | Journal-specific instructions control. For LaTeX, journals commonly request a review PDF plus a `.zip`/`.tar` source archive. Metadata commonly requested includes authors, affiliations, contributor roles, funding, and keywords. Filenames should be unique, anonymous, use standard extensions, and be no more than 80 characters. | The flat source archive and PDF are appropriate in principle, but the Owner must confirm WPI's exact file roles, metadata, and filename rules in the live system. |
| [Is there a submission checklist I can use?](https://www.elsevier.support/publishing/answer/is-there-a-submission-checklist-i-can-use) | The generic checklist covers corresponding-author details, keywords, figures/captions, tables/legends, reference consistency, permissions, and an AI-use declaration when applicable. | These checks are represented in `FINAL_SUBMISSION_GATE.md`; journal-specific requirements still control. |
| [What are Conflict of Interest Statements, Funding Source Declarations, Author Agreements/Declarations and Permission Notes?](https://www.elsevier.support/publishing/answer/what-are-conflict-of-interest-statements-funding-source-declarations-author-agreementsdeclarations-and-permission-notes) | Authors must state explicitly whether competing interests exist; the Owner-verified current new-submission experience treats both the manuscript and Declaration of Competing Interests as mandatory across journals. | Keep the manuscript declaration and upload the prepared separate declaration, or complete the equivalent declaration interaction shown by the live system. |
| [Video Guide: Submitting a LaTeX file in Editorial Manager](https://www.elsevier.support/publishing/answer/video-guide-submitting-a-latex-file-in-editorial-manager) | Elsevier provides a dedicated LaTeX upload workflow. | Use the validated flat `WPI_LaTeX_Source.zip`; inspect the live file-role labels before upload. |
| [How can I transfer my rejected manuscript using Transfer Your Manuscript?](https://www.elsevier.support/publishing/answer/how-can-i-transfer-my-rejected-manuscript-using-transfer-your-manuscript) and [Article Transfer Service author overview](https://www.elsevier.support/publishing/answer/video-guide-article-transfer-service-author-overview) | Transfer is optional and author-controlled. A confirmed transfer creates a new submission that is not complete until the author acts; the transferred submission expires after 90 days if not completed. | This package is a direct WPI submission package, not a transfer package. If transfer is later used, re-check WPI-specific metadata, declarations, and files in the new submission. |

## Additional Support Center navigation supplied by the Owner

The following are Support Center category pages rather than journal-specific
instructions. They are useful navigation aids but do not replace the WPI Guide
for Authors or live Editorial Manager fields.

| Category | Gate interpretation |
|---|---|
| [Submission instructions](https://www.elsevier.support/publishing/category/10611) | Routes to current submission help. Individual answer pages and WPI-specific instructions remain controlling. |
| [LaTex Issue](https://www.elsevier.support/publishing/category/17993) | Routes to LaTeX troubleshooting. The package's successful clean rebuild is the local evidence for source integrity; this category does not add a WPI-specific upload requirement. |
| [Transfer article to another journal](https://www.elsevier.support/publishing/category/10609) | Applies only if an article-transfer workflow is used. This package remains a direct WPI submission. |

## Current conclusions for journal_09

- The package's PDF, flat LaTeX archive, figures, highlights, cover letter, and
  manuscript declarations remain valid repository artifacts. A separate
  `Declaration_of_Competing_Interests.docx` is also prepared.
- The Owner's current-policy decision treats the manuscript and Declaration of
  Competing Interests as mandatory across journals. The exact live Item Type or
  form interaction remains a submission-time check, not a package-readiness
  blocker.
- The generic checklist's AI wording is not used to overwrite the manuscript's
  exact policy heading. The manuscript retains the requested heading from the
  current Elsevier generative-AI policy note.
- WPI's public Editorial Manager landing page and its official Instructions for
  Authors link were verified. Exact Item Type assignment and other live fields
  remain Owner submission-time checks because they are visible only inside the
  active workflow; they do not block the prepared artifact.
