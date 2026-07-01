---
layout: page
title: Pipeline de análisis
permalink: /pipeline/
type: extras
description: Cómo se generan las visualizaciones a partir de los archivos TEI
icon: book
---

Todas las visualizaciones de este sitio se generan de forma reproducible a partir de los archivos TEI-XML mediante un conjunto de scripts en Python.

El procedimiento parte del marcado de citas (`persName`, `placeName`, `bibl`) en los seis números, construye una **red de citas** dirigida (con [NetworkX](https://networkx.org/)), detecta **comunidades intelectuales**, calcula medidas de **centralidad** (grado, PageRank e intermediación) y exporta los datos que alimentan cada visualización.

El código está disponible en el directorio [`visualizations/`](https://github.com/hdlabconicet/revista-sitio-digital/tree/main/visualizations) del repositorio. Para regenerar las visualizaciones desde el XML:

```bash
pip install lxml networkx pyvis pandas matplotlib fa2
python -m visualizations.run_all
```

Los módulos principales son `tei_parser.py` (lectura del TEI), `network_analysis.py` (construcción y métricas de la red), `prosopography_analysis.py` (análisis de las figuras) y los distintos `export_*.py` (exportación a cada visualización).
