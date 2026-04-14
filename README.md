# Curso de Claude Code de Platzi
## Profe

- Eduardo Alvarez

## Distribución del carpetas

- Backend
- Frontend
- Mobile


Prompt 1

analiza el proyecto y entiende cómo es la arquitectura que tiene, es importante que entiendas que hay más de un proyecto contenido en él @Backend/ @Frontend/ @Mobile/
Utiliza a estas carpetas para crear un big picture completo de la arquitectura del sistema

prompt 2
gracias, excelente analisis de arquitectura, ahora con esta     
  informacion que tienes en el contexto crear el archivo 
  claude.md para que se pueda usar como memoria para el resto del 
  desarrollo del proyecto 

prompt 3

Ahora ayudame a tener el servicio de @Backend\ corriendo local,   ya tengo instalado docker 

prompt 3

necesito implementar un sistema de ratings en este proyecto, el rating de un curso puede ir desde 1 estrella hasta 5 estrellas. Tu tarea es analizar el impacto que va a tener la implementación de este feature en el proyecto. Analiza qué acciones deben hacerse en cada uno de los componentes del proyecto (backend, frontend) para implementar el rating

@"architect (agent)" Utiliza el contexto que tenemos de la      
  conversacion para el analisis del impacto que debes hacer,      
  apoyate en lo que ya esta descubierto y crea el plan de         
  implementacion 
  
prompt 4
   ahora guarda utilizando el formato que tiene el subagente de
  architect el plan de implementación dentro del proyecto,         
  guardalo en una carpeta en el root que se llame spec y dale un
  nombre adecuado con esta nomenclatura 00_nombre_del_spec.md, 00
  es un número que incrementará a lo largo que se creen más      
  specs      

prompt 5

analiza el @spec/01_plan_ratings.md que es el análisis que uso tu subagente de architect, utilizando esto como referencia utiliza a los subagentes de backend y de frontend para crear un plan específico de implementación, no generes código sino que crea únicamente las fases que se harán en la implementacion
