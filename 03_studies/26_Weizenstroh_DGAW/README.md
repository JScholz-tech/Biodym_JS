# Case Study: Weizenstroh (Wheat Straw) — DGAW 2026

This folder contains the input data and output figures for the wheat straw cascading case study presented at the **Deutsche Gesellschaft für Abfallwirtschaft (DGAW)** conference.

## Citation

If you use this case study or its results, please cite:

> Scholz, J. (2026). BioDYM: Material Flow Analysis of Wheat Straw Cascading Systems.
> *Proceedings of the DGAW Annual Conference.*
> DOI: [10.15203/99106-187-8](https://doi.org/10.15203/99106-187-8)

A machine-readable citation is provided in [CITATION.bib](CITATION.bib).

## Folder Structure

```
26_Weizenstroh_DGAW/
├── input/
│   └── 260218_bioDYM_Systemmanager_template_DGAW_Weizenstroh_final.xlsm   # BioDYM input file
├── output/
│   ├── 260215_CC_DSM.png        # Carbon content — Dynamic Stock Model results
│   ├── 260215_CC_FOMP.png       # Carbon content — First-Order Mineralization Process results
│   ├── 260215_CC_Stock.png      # Carbon content — Stock evolution
│   ├── 260216_MC_500.png        # Monte Carlo uncertainty analysis (500 iterations)
│   └── Weizenstroh_DGAW.png     # Summary figure for DGAW presentation
├── CITATION.bib                  # Bibliographic reference (BibTeX)
├── LICENSE                       # CC BY 4.0 — data and figures
└── README.md                     # This file
```

## Reproducing the Results

1. Open `input/260218_bioDYM_Systemmanager_template_DGAW_Weizenstroh_final.xlsm` in Excel.
2. Run the BioDYM workflow notebook (`00_BioDYM_Workflow.ipynb`) from the repository root.
3. Output figures will be written to `01_data/02_output/figures/`.

## License

The figures and data in this folder are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
See [LICENSE](LICENSE) for the full license text.

The BioDYM software itself is licensed under the **MIT License** (see repository root).
