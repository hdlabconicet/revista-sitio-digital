---
layout: page
title: Acerca de
permalink: /acerca-de/
type: extras
---

<div class="prose" markdown="1">

## La revista

*Revista SITIO* fue una publicación literaria y cultural argentina aparecida en Buenos Aires entre **1981 y 1987**, dirigida por **Ramón Alcalde, Eduardo Grüner, Luis Gusmán, Jorge Jinkis, Mario Levin y Luis Thonis**. Surgida en los últimos años de la dictadura militar y la transición democrática, fue —junto a *Punto de Vista* y *Babel*— una de las revistas intelectuales clave del período.

Frente a la tradición de revistas que abordaban la literatura sobre todo como evidencia para el análisis social y cultural, *SITIO* propuso una reorientación radical: interpretar los fenómenos externos *a través* de la literatura, tratando la lectura como una práctica irreductible y no como un medio para acceder a un conocimiento extraliterario.

## El proyecto

Esta edición crítica digital explora *Revista SITIO* con herramientas de edición digital y de análisis computacional, con el objetivo de exhibir y reflexionar sobre las tensiones entre lectura y ensayo que caracterizaron a la publicación. El proyecto está dirigido por el **Dr. Federico Cortés** en el marco de una beca del programa **Georg Forster** de la **Fundación Alexander von Humboldt**, y se desarrolla en el **HD LAB** (IIBICRIT, CONICET).

## Metodología

La edición comprende:

- El **reconocimiento óptico de caracteres (OCR)** de la edición facsimilar con **Transkribus**, para el cual entrenamos un modelo específico de reconocimiento de español impreso en revistas literarias.
- La **codificación TEI-XML** de los seis números de la revista, con marcado de personas, lugares, obras y organizaciones citadas.
- Un **pipeline de análisis** en Python que, a partir de ese marcado, construye la red de citas, detecta comunidades intelectuales y calcula medidas de centralidad.
- Seis **visualizaciones interactivas** que ofrecen distintas lecturas de esa red.

Puede consultar los detalles del procedimiento en la sección [Recursos]({{ site.baseurl }}/recursos/).

## La edición en cifras

- **6** números codificados (1981–1987).
- **919** personas identificadas y **269** lugares.
- **632** referencias bibliográficas citadas.
- Una red de **767 figuras** conectadas por **1347 citas**, organizadas en **13 comunidades intelectuales**.
- **36** colaboradores/as de la revista y **731** figuras citadas.

## Créditos

- **Dirección del proyecto:** Federico Cortés.
- **Edición digital (TEI):** Federico Cortés y Juan Manuel Franca.
- **Edición y coordinación:** Federico Cortés, Gimena del Rio Riande y Gabriel Calarco.

Esta edición se comparte bajo licencia [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### Cómo citar

Cortés, Federico, Franca, Juan Manuel, del Rio Riande, Gimena, Calarco, Gabriel (eds.). (2026). *Revista SITIO. Edición crítica digital*. HD LAB. <{{ site.url }}{{ site.baseurl }}/>. ISSN 3072-7715 [Fecha de consulta].

</div>
