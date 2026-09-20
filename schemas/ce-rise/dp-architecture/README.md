# CE-RISE DPP & DMP Architecture Documentation

This repository contains the source files for the CE-RISE Digital Product and Material Passport (DPP & DMP) data model architecture documentation website, published at: [https://ce-rise-models.codeberg.page/dp-architecture/](https://ce-rise-models.codeberg.page/dp-architecture/)

The documentation website explains the approach to data modeling developed and adopted in the CE-RISE project for Digital Product and Material Passports. **For the actual documentation content, please visit the published website.**

## Repository Purpose

This repository serves as:
- Source for the documentation website built with MkDocs Material
- Version control for documentation content and structure
- CI/CD pipeline for automatic website deployment

## Updating Documentation

### Prerequisites

- Python 3.x
- MkDocs Material theme

### Local Development

1. Clone the repository:
   ```bash
   git clone https://codeberg.org/ce-rise-models/dp-architecture.git
   cd dpp-architecture
   ```

2. Install dependencies:
   ```bash
   pip install mkdocs-material
   ```

3. Start local development server:
   ```bash
   mkdocs serve
   ```

4. View the site at `http://localhost:8000`

### Adding Content

1. Create or edit Markdown files in the `docs/` directory
2. Update the navigation structure in `mkdocs.yml` if adding new pages
3. Commit and push changes to the `main` branch

### Automatic Deployment

The documentation website is automatically built and deployed via Forgejo Actions when changes are pushed to the `main` branch. The workflow:

1. Builds the MkDocs site
2. Deploys to Codeberg Pages
3. Makes the site available at the published URL

### File Structure

```
├── docs/                     # Documentation source files
│   ├── index.md                      # Homepage content
│   ├── stylesheets/                  # Custom CSS
│   └── logo.png                      # CE-RISE logo
│   └── ...                           # Rest of the documentation files
├── mkdocs.yml                # MkDocs configuration
└── .forgejo/workflows/       # CI/CD pipeline to publish documentation
└── .github/workflows/        # CI/CD pipeline to archive releases on Zenodo
```

---


---
<a href="https://europa.eu" target="_blank" rel="noopener noreferrer">
  <img src="https://ce-rise.eu/wp-content/uploads/2023/01/EN-Funded-by-the-EU-PANTONE-e1663585234561-1-1.png" alt="EU emblem" width="200"/>
</a>

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.  
Views and opinions expressed are those of the author(s) only and do not necessarily reflect those of the European Union or the granting authority (HADEA).  
Neither the European Union nor the granting authority can be held responsible for them.

© 2025 CE-RISE consortium.  
Licensed under [Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" width="40"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
