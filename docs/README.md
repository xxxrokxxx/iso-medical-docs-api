# ISO Standard Documents

This directory should contain the ISO standard PDF files for indexing.

## Required Documents

The system was designed to work with the following ISO medical device standards:

1. **ISO 13485:2016** - Medical devices — Quality management systems
2. **ISO 14971:2019** - Medical devices — Application of risk management
3. **ISO 14155:2020** - Clinical investigation of medical devices for human subjects
4. **ISO 62304:2006** - Medical device software — Software life cycle processes
5. **ISO 15223-1:2021** - Medical devices — Symbols to be used with information
6. **EU MDR 2017/745** - Medical Device Regulation
7. **MDCG 2020-3** - Clinical evaluation guidance

## How to Obtain PDFs

⚠️ **Note**: Due to licensing restrictions and file size limitations, PDF files are not included in this repository.

### Option 1: Purchase from ISO
- Visit: https://www.iso.org/standards.html
- Search for the standard number (e.g., "ISO 14971")
- Purchase and download the PDF

### Option 2: Organizational Access
- If your organization has an ISO subscription, download from your portal
- Many companies have enterprise licenses for ISO standards

### Option 3: National Standards Bodies
- Many countries have their own standards organizations (e.g., ANSI in USA, BSI in UK)
- These often provide access to ISO standards

## Setup Instructions

1. Obtain the PDF files through one of the methods above
2. Place all PDF files in this `docs/` directory
3. Run the data ingestion script:
   ```bash
   python create_iso_collection.py
   ```

## File Naming

The system accepts any PDF filename. The original filenames used were:
- `ISO 13485-2016 ed.3 - id.59752 Publication PDF (en).pdf`
- `ISO 14971-2019 ed.3 - id.72704 Publication PDF (en).pdf`
- `EVS_EN_ISO_14155-2020+A11-2025_en.pdf`
- `EVS_EN_62304-2006+A1-2015_en.pdf`
- `EVS_EN_ISO_15223_1-2021_en.pdf`
- `CELEX_32017R0745_EN_TXT.pdf`
- `MDCG_2020-3_en_Rev1.pdf`

You can use any naming convention as long as they're PDF files.

## Alternative: Use Your Own Documents

This system can work with **any PDF documents**, not just ISO standards. Simply:
1. Place your PDF files in this directory
2. Run `create_iso_collection.py` to index them
3. The RAG system will work with your custom documents

## Data Already Indexed?

If you're deploying this application and the Weaviate collection is already populated with document chunks, **you don't need the PDF files**. The PDFs are only required for:
- Initial data ingestion
- Re-indexing documents
- Adding new documents to the collection

## Questions?

See the main [README.md](../README.md) for full setup instructions.
