# 🛒 E-Commerce Listing Automation System

A smart and automated system for extracting product data from e-commerce websites and generating optimized listings with AI-powered content.

## ✨ Features

- **🔍 Smart Product Search**: Search for products by name across multiple e-commerce platforms
- **🤖 AI Content Generation**: Automatically generate product descriptions and content
- **📸 Image Processing**: Download and optimize product images
- **📊 Data Export**: Export to Excel with structured product data
- **☁️ Google Drive Integration**: Upload images to Google Drive
- **📈 Analytics Dashboard**: Visual insights into processed products
- **🎨 Modern UI**: Beautiful Streamlit interface with real-time progress tracking

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```

**Note**: This step is crucial! Playwright requires browser binaries to be installed separately.

### 3. Setup Google Drive (Optional)

1. Place your `client_secrets.json` file in the project root
2. The system will authenticate automatically when needed

### 4. Run the Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 📱 Using the Streamlit Interface

### 🏠 Dashboard
- **Overview**: See total processed products, success rate, and system status
- **Metrics**: Real-time statistics and processing status
- **Recent Products**: View recently processed products with details

### 🔍 Product Processing

#### Option 1: Search by Product Name
1. Enter a product name (e.g., "HP 320 FHD Webcam")
2. Select number of results to process (1-10)
3. Click "Search & Process"
4. Review found URLs and click "Process All Products"

#### Option 2: Direct URL Processing
1. Paste a direct product URL
2. Click "Process URL"
3. View detailed results immediately

#### Option 3: Batch Excel Upload
1. Upload an Excel file with product URLs
2. Preview the data
3. Click "Process Excel Data"
4. Monitor batch processing progress

### 📋 Recent Products
- View all recently processed products
- Download data as CSV
- See processing timestamps and details

### ⚙️ Settings
- **Google Drive**: Connect/disconnect Google Drive
- **Data Management**: Clear processed data or open data folder

## 🔧 Configuration

### API Keys
The system uses several APIs that are pre-configured:

- **Together.ai**: For AI content generation
- **SerpAPI**: For product search and brand/category extraction
- **Google Drive**: For image storage (optional)

### Supported E-commerce Sites
- Amazon India
- Flipkart
- Croma
- Reliance Digital
- TataCliq
- Vijay Sales
- Snapdeal
- Paytm Mall
- ShopClues
- Myntra
- AJIO
- Nykaa

## 📊 Output Format

The system generates structured data including:

- **Product Title**: Extracted from the source
- **Short Description**: AI-generated summary
- **Full Content**: Detailed HTML-formatted description
- **Brand & Category**: Automatically detected
- **Price**: Current product price
- **Images**: Optimized product images
- **Part Code/SKU**: Product identifier
- **Processing Metadata**: Timestamps and source URLs

## 🎯 Key Features

### Smart Processing
- **Domain Diversity**: Ensures products from different e-commerce sites
- **Error Handling**: Graceful handling of failed scrapes
- **Progress Tracking**: Real-time progress bars and status updates
- **Data Validation**: Checks for valid product data before processing

### AI Integration
- **Content Generation**: Creates engaging product descriptions
- **Brand Detection**: Automatically identifies product brands
- **Category Classification**: Categorizes products intelligently
- **HTML Formatting**: Converts plain text to formatted HTML

### Visual Analytics
- **Category Distribution**: Pie charts showing product categories
- **Brand Analysis**: Bar charts of processed brands
- **Processing Metrics**: Success rates and processing statistics
- **Real-time Updates**: Live dashboard with current status

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit web interface
- **Backend**: Python modules for scraping, processing, and AI
- **Data Storage**: Excel files and Google Drive
- **APIs**: Multiple external APIs for enhanced functionality

### Modules
- `scraper.py`: Web scraping functionality
- `content_generator.py`: AI content generation
- `image_processor.py`: Image download and optimization
- `excel_exporter.py`: Data export and formatting
- `content_formatter.py`: HTML content formatting
- `drive_uploader.py`: Google Drive integration

## 🚨 Troubleshooting

### Common Issues

1. **API Rate Limits**: If you hit API limits, wait a few minutes and retry
2. **Access Denied**: Some sites may block automated access
3. **Image Download Failures**: Check internet connection and file permissions
4. **Google Drive Issues**: Ensure `client_secrets.json` is properly configured

### Performance Tips

- Process products in smaller batches for better reliability
- Use direct URLs for faster processing
- Ensure stable internet connection for image downloads
- Monitor system resources during batch processing

## 📈 Future Enhancements

- [ ] Support for more e-commerce platforms
- [ ] Advanced AI content customization
- [ ] Real-time price monitoring
- [ ] Automated listing updates
- [ ] Multi-language support
- [ ] Advanced analytics and reporting

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving documentation
- Adding support for new e-commerce sites

## 📄 License

This project is for educational and commercial use. Please respect the terms of service of the e-commerce platforms you're scraping.

---

**Happy E-commerce Automation! 🛒✨** 