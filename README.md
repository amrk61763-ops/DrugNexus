# DrugNexus

> A scientific drug information platform connecting pharmaceutical products in the Egyptian market with active ingredients, chemical information, and structural data.

[![Live Demo](https://img.shields.io/badge/Live-Demo-informational)](https://drug-nexus.vercel.app/)
[![API Docs](https://img.shields.io/badge/API-Swagger%20Docs-informational)](https://drug-nexus.vercel.app/docs)
[![License](https://img.shields.io/badge/License-Source--Available-lightgrey)](LICENSE)

---

## Live Demo

**Website:**  
https://drug-nexus.vercel.app/

**Interactive API Documentation:**  
https://drug-nexus.vercel.app/docs

---

## Overview

DrugNexus is a pharmaceutical and scientific information platform developed around the Egyptian pharmaceutical market.

The project connects pharmaceutical trade names with their active ingredients and extends those relationships into scientific and structural information.

The core idea is:

**Trade Name → Active Ingredient → Scientific Information → Structural Data**

The first version was built as a practical exploration of how pharmaceutical knowledge, structured data, APIs, databases, and scientific resources can be combined into a single usable platform.

---

## What DrugNexus Does

### Pharmaceutical Search

DrugNexus provides search capabilities for pharmaceutical products using their trade names and active ingredients.

Users can move between a pharmaceutical product and the active ingredient associated with it.

### Active Ingredient Information

Active ingredient records can be connected with scientific identifiers and external scientific resources.

Depending on the available data, information may include:

- Molecular information
- Pharmacological information
- Mechanism of action
- Molecular mechanism
- Pharmacodynamics
- Half-life
- Toxicological information
- Hazard information
- MeSH information
- ChEMBL-related information
- Structural information

### Structural Information

DrugNexus extends the pharmaceutical information layer into structural biology.

Where relevant structural data is available, active ingredients can be associated with Protein Data Bank (PDB) structures, receptors, and ligands.

The project also includes processed ligand files intended to provide a convenient starting point for computational chemistry workflows such as molecular docking.

---

## Dataset

The initial version focuses on the Egyptian pharmaceutical market and covers approximately:

- **14,000+ trade names**
- **1,700+ active ingredients**

Active ingredients are associated with scientific identifiers and information obtained from external scientific resources where available.

The production database is not included in this repository.

---

## Scientific Data Sources

DrugNexus connects information from external scientific resources, including:

- **PubChem**
- **ChEMBL**
- **Protein Data Bank (PDB)**

DrugNexus acts as an organization and discovery layer around relevant information.

It does not replace the original scientific databases.

Users should consult the original data providers for authoritative source information and applicable terms of use.

---

## PDB / Ligand Pipeline

One of the project's additional components is a structural-data pipeline.

The purpose of the pipeline is to move from available structural records toward more useful ligand files for computational workflows.

Conceptually:

```text
Active Ingredient
       ↓
Structural Search
       ↓
PDB Structure
       ↓
Ligand Identification
       ↓
Quality Filtering
       ↓
Ligand Processing
       ↓
Prepared Structural File
