---
layout: page
title: Análisis textual automatizado
permalink: /voyant/
type: extras
description: Estadísticas textuales y visualizaciones del texto realizadas con Voyant Tools
icon: bar-chart
---

Exploración del contenido de _Viaje al Río de la Plata_ con [Voyant Tools](https://voyant-tools.org/), una herramienta de lectura distante y análisis estadístico de textos digitales.

Las siguientes secciones presentan cuadros interactivos. En cada panel, deslice el cursor sobre la esquina derecha de la barra superior para mostrar las opciones. El ícono <i class="fa-solid fa-question" style="color:#157fcc;"></i> permite acceder a una explicación de la herramienta usada en cada panel. El ícono <i class="fa-solid fa-toggle-on" style="color:#157fcc;"></i> permite modificar las opciones de la herramienta.

## Nube de palabras

Palabras más frecuentes del texto de Ulrico Schmidel. Deslice el cursor sobre las palabras para ver la frecuencia en el texto.

<iframe class="py-3" src='https://voyant-tools.org/tool/Cirrus/?stopList=keywords-64a7303ec8f6f565c2d9acf045f45552&corpus=d032fba88ac0d35198eb74f591f71ef0'></iframe>

Deslice la barra de términos para aumentar o disminuir la cantidad de palabras en la nube.

## Contextos

Contexto enunciativo de las palabras más frecuentes del texto. Puede modificar por frecuencia ascendente o descendente.

<iframe class="py-3" src='https://voyant-tools.org/tool/Contexts/?stopList=keywords-64a7303ec8f6f565c2d9acf045f45552&query=%C3%A1&corpus=d032fba88ac0d35198eb74f591f71ef0'></iframe>

Modifique el término a consultar desde el menú inferior izquierdo.

## Tendencias

Evolución de la frecuencia de los principales términos del _Viaje al Río de la Plata_.

<iframe class="py-3" src='https://voyant-tools.org/tool/Trends/?stopList=keywords-64a7303ec8f6f565c2d9acf045f45552&query=tierra&query=gente&query=capit%C3%A1n&query=nuestro&mode=document&corpus=d032fba88ac0d35198eb74f591f71ef0'></iframe>

## Grafo de colocaciones

Deslice el cursor sobre las palabras de este grafo de colocaciones para consultar la frecuencia de cada par de términos.

<iframe class="py-3" src='https://voyant-tools.org/tool/CollocatesGraph/?stopList=keywords-96bb75df7f437a2c04c666669c74a2cf&query=capit%C3%A1n&corpus=d032fba88ac0d35198eb74f591f71ef0'></iframe>

<div class="py-4 mt-4"><p>Visite <a href="https://voyant-tools.org/?corpus=d032fba88ac0d35198eb74f591f71ef0" target="_blank">este link</a> para descubrir el <i>Viaje al Río de la Plata</i> a la luz de otras herramientas ofrecidas por Voyant Tools: <a href="https://voyant-tools.org/?corpus=d032fba88ac0d35198eb74f591f71ef0&view=bubbles" target="_blank">burbujas</a>, <a href="https://voyant-tools.org/?corpus=d032fba88ac0d35198eb74f591f71ef0&view=loom" target="_blank">Loom</a>, y muchas más.</p></div>
