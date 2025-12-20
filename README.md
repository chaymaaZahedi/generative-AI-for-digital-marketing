# Generative AI for Digital Marketing

Welcome to the **Generative AI for Digital Marketing** repository. This project serves as a comprehensive suite of AI-powered tools designed to revolutionize digital marketing workflows. It bridges the gap between high-quality visual content preparation and intelligent professional networking.

The repository is divided into two main modules, each targeting a specific aspect of the digital marketing lifecycle:

## 📂 Project Modules

### 1. 🖼️ PrintPrep-AI (Image Optimization & Print Readiness)
**Location:** [`/PrintPrep-AI`](./PrintPrep-AI)

A powerful tool focused on ensuring your visual assets are of the highest quality and ready for professional printing.
*   **Upscaling:** Enhance image resolution using advanced AI models like RealESRGAN and Lanczos interpolation.
*   **Enhancement:** Apply denoising and sharpening to perfect your visuals.
*   **Print Assurance:** Automatic DPI calculation and quality checks.
*   **Professional Standards:** Complete support for CMYK conversion, Soft Proofing with ICC profiles, and PDF/X-1a export ensuring industry-standard print compatibility.

[👉 Explore PrintPrep-AI](./PrintPrep-AI/README.md)

### 2. 🤖 LinkedIn Intelligent Agent (Scraping & Outreach)
**Location:** [`/Linkedin_scrapper`](./Linkedin_scrapper)

An autonomous agent designed to automate and supercharge your professional networking and lead generation efforts.
*   **Deep Scraping:** Safely extract enriched profile data using advanced MCP (Model Context Protocol) and Playwright.
*   **AI Enrichment:** leverages Claude-Sonnet to infer details like gender and age from profile data.
*   **Smart Database:** Centralized SQLite storage with advanced filtering capabilities.
*   **Outreach:** Integrated email campaign manager with customizable templates.
*   **Autonomous Operation:** A goal-oriented agent that can execute complex search and save tasks independently.

[👉 Explore LinkedIn Scrapper](./Linkedin_scrapper/README.md)

---

## 🚀 Getting Started

To get started with either module, please navigate to the respective directory and follow the detailed installation and usage instructions provided in their specific `README.md` files.

### General Prerequisites
*   **Python 3.10+**
*   **Git**

### Installation Overview
1.  Clone this repository:
    ```bash
    git clone <repository_url>
    cd generative-AI-for-digital-marketing
    ```
2.  Navigate to the desired module:
    ```bash
    # For Image Tools
    cd PrintPrep-AI

    # For LinkedIn Tools
    cd Linkedin_scrapper
    ```
3.  Follow the setup steps inside the module's documentation.

---

## 🛠️ Key Technologies

This project harnesses the power of modern AI and web frameworks:

*   **Core Framework:** Python, FastAPI
*   **AI & LLMs:** Claude-Sonnet, RealESRGAN
*   **Web Automation:** Playwright, Model Context Protocol (MCP)
*   **Data & Print:** SQLite, Pillow, ICC Profiles
*   **Frontend:** HTML5, CSS3, Jinja2

---

## 📄 Documentation

For more detailed project background and theoretical underpinnings, please refer to the included project documentation:
*   [`IA_gen_project_img_gen.pdf`](./IA_gen_project_img_gen.pdf)
*   [`rapport_projet_gen_IA.pdf`](./rapport_projet_gen_IA.pdf)

