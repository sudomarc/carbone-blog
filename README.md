# carbone-blog

A modern, lightweight HTML blog built with Carbone.

## Overview

carbone-blog is a clean and minimalist blog platform built entirely in HTML. It provides a simple way to create and manage blog posts without heavy frameworks or dependencies.

## Features

- 📝 Clean, semantic HTML structure
- 🎨 Minimal and responsive design
- ⚡ Fast loading and performance
- 📱 Mobile-friendly layout
- 🔍 SEO-optimized markup
- 📚 Easy to customize and extend

## Getting Started

### Prerequisites

- A web server or local development environment
- A modern web browser

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Patrickk2/carbone-blog.git
```

2. Navigate to the project directory:
```bash
cd carbone-blog
```

3. Open `index.html` in your browser or serve the files with a local server:
```bash
# Using Python 3
python -m http.server 8000

# Using Node.js
npx http-server
```

## Project Structure

```
carbone-blog/
├── index.html          # Main landing page
├── posts/              # Blog post files
├── css/                # Stylesheets
├── js/                 # JavaScript files
├── img/                # Images and assets
└── README.md          # This file
```

## AI Article Generation

The publishing workflow uses **NVIDIA NIM by default**.

1. Add the repository secret `NVIDIA_API_KEY` in GitHub → Settings → Secrets and variables → Actions.
2. Keep `NEWS_API_KEY` configured for source retrieval.
3. Optionally set the repository variable `NVIDIA_MODEL` (default: `nvidia/nemotron-3.5-lightning-30b-a3b`) and `NVIDIA_MAX_TOKENS` (default: `2048`).

NVIDIA NIM uses the OpenAI-compatible `/v1/chat/completions` endpoint at `https://integrate.api.nvidia.com/v1`.

**OpenRouter is retained as a legacy provider**, not the default. To use it deliberately, set the repository variable `AI_PROVIDER=openrouter` and provide the `OPENROUTER_API_KEY` secret. Its model and fallback settings remain available through `OPENROUTER_MODEL` and `OPENROUTER_FALLBACK_MODELS`.

## Creating Blog Posts

1. Create a new HTML file in the `posts/` directory
2. Follow the template structure from existing posts
3. Add the post to the index/archive page
4. Customize styling as needed

## Customization

- Modify CSS files in the `css/` directory for styling changes
- Update the site title and metadata in the `<head>` section of HTML files
- Add JavaScript functionality in the `js/` directory

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to help improve the blog.

## Author

**Patrick** - [GitHub Profile](https://github.com/Patrickk2)

## Contact

For questions or suggestions, please open an issue on this repository.

---

*Last updated: April 25, 2026*