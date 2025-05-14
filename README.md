# QDMBoxSearch

A quick and dirty desktop application for searching through large mbox files. Built with Python and PyQt6.

## Features

- Fast search through large mbox files (tested with 20GB+ files)
- Modern, native-looking interface
- Cross-platform support (macOS, Windows, Linux)
- HTML email rendering support
- Real-time progress indication
- Platform-specific menu integration

## Installation

### Pre-built Executables

Download the latest release for your platform from the [Releases](https://github.com/jfdurocher/QDMboxSearch/releases) page.

### From Source

1. Clone the repository:
```bash
git clone https://github.com/jfdurocher/QDMboxSearch.git
cd QDMboxSearch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python mbox_search_gui.py
```

## Building from Source

To build standalone executables:

1. Install build dependencies:
```bash
pip install pyinstaller pillow pyqt6
```

2. Run the build script:
```bash
python build.py
```

The executable will be created in the `dist/QDMBoxSearch` directory.

## Usage

1. Launch the application
2. Click "File > Open" or use Cmd/Ctrl+O to select an mbox file
3. Wait for the file to load (progress will be shown)
4. Use the search box to find messages
5. Click on any message in the results to view its content

## Development

- Python 3.8+
- PyQt6 for the GUI
- PyInstaller for building executables

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

J.F. Durocher (jf@durocher.in)

## Acknowledgments

- PyQt6 team for the excellent GUI framework
- Python community for the amazing tools and libraries 