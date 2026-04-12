# Revista SITIO — Edición Crítica Digital

Edición digital de *Revista SITIO* (Buenos Aires, 1981-1987), una publicación literaria y cultural argentina dirigida por Ramón Alcalde, Eduardo Grüner, Luis Gusmán, Jorge Jinkis, Mario Levin y Luis Thonis. Aparecida durante los últimos años de la dictadura militar y la transición democrática, *SITIO* fue una de las revistas intelectuales clave del período, junto a *Punto de Vista* y *Babel*.

Frente a la tradición "culturalista" representada por revistas como *Contorno* y *Punto de Vista*, que abordaban la literatura principalmente como evidencia para el análisis social y cultural, *SITIO* propuso una reorientación radical: interpretar los fenómenos externos a través de la literatura, tratando la lectura como una práctica irreductible y no como un medio para acceder a un conocimiento extraliterario.

## Contenido

Esta edición digital comprende:

- **Codificación TEI-XML** de los seis números de la revista (1981-1987), con marcado de personas, lugares, obras y organizaciones citadas.
- **Visualizaciones interactivas** de la red de citas: explorador de red, comunidades intelectuales, biografías de figuras citadas, afinidades editoriales, flujos de citación y figuras de "resistencia".
- **Pipeline de análisis** en Python para regenerar las visualizaciones a partir de los archivos TEI fuente.

### Estructura del repositorio

```
revista-sitio-digital/
├── TEI/                    # Archivos TEI-XML fuente
│   ├── issue_1.xml ... issue_6.xml
│   ├── listPerson.xml
│   ├── listBibl.xml
│   ├── listPlaces2.xml
│   └── listEd2.xml
│
├── visualizations/         # Pipeline de análisis (Python)
│
├── sigma-viz/              # Explorador de red (Sigma.js)
├── map/                    # Comunidades intelectuales
├── timeline/               # Biografías de figuras
├── contributors/           # Afinidades editoriales
├── flows/                  # Flujos de citación
├── shadows/                # Resistencias
│
├── shared/                 # Estilos compartidos
└── server.py               # Servidor HTTP local para desarrollo
```

## Cómo usar

### Visualizar localmente

```bash
python server.py
```

Luego abrir `http://localhost:9000` en el navegador y navegar entre las visualizaciones.

### Regenerar las visualizaciones desde el XML

```bash
pip install lxml networkx pyvis pandas matplotlib fa2
python -m visualizations.run_all
```

## Editores digitales

Federico Cortés y Juan Manuel Franca.

## Licencia

Los materiales de esta edición están publicados bajo licencia [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](LICENSE).
