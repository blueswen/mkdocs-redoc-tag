---
hide:
  - navigation
  - toc
---

When using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) you can [hide the sidebar](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#hiding-the-sidebars) to get full width Redoc on the page.

## Markdown

```html
---
hide:
  - navigation
  - toc
---

<redoc src="https://petstore.swagger.io/v2/swagger.json"/>
```

## Redoc

<redoc src="https://petstore.swagger.io/v2/swagger.json" />
