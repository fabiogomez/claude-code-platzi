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

make build
make start


@Backend/Makefile  tenemos comandos para poner a correr el servicios local, agrega un comando que permita ejcutar las pruebas dentro del       contenedor ignora si ya existe 


ejecuta el comando de pytest dentro del contenedor de api para verificar que el servicio este funcionando  



@spec/01_backend_ratings_implementation_plan.md empecemos la implementación de la fase 1 de este plan, es necesario que los comandos que vayas a ejecutar sean dentro del contenedor de API porque es el lugar en el que está siendo ejecutado. en el archivo de @Backend/Makefile hay varios comandos que resultarán útiles para poder construir y reiniciar la imagen de docker si es necesario


7. "ultrathink @spec/01b_plan_ratings_backend.md d empecemos la implementación de la 
  fase 1 de este plan, es necesario que los comandos que vayas a ejecutar sean dentro  
  del contenedor de API..."
  8. "garantiza que el servicio sigue corriendo ejecutando los unit test, reinicia el  
  servicio si es necesario para tomarlos nuevos cambios"
  9. "marca en @..\spec\01b_plan_ratings_backend.md como completadas las fases ya      
  completadas"
  10. "@..\spec\01b_plan_ratings_backend.md implementa las fases que faltan y marcalas 
  como completadas una vez terminadas"
  11. "/security-review"
  12. "guarda estos hallasgos de seguridad en un nuevo spec en la carpeta @specs"      
  13. "I am triying to run the frontend with yarn dev and getting this error"
  14. "yarn run v1.22.22 ... 'next' no se reconoce..."
  15. "getting this error when i start the app"
  16. "async function getCourses(): Promise<Course[]> { > 7 | const res = await        
  fetch..."
  17. "getting this error TypeError: Cannot read properties of undefined (reading      
  'map')"
  18. "@"frontend (agent)" implementa el plan @spec/01a_plan_ratings_frontend.md"      
  19. "getting this error [Image #1]" (rating form error screenshot)
  20. "/give" (unknown command — typo, possibly meant /ide)
  21. "show me the last prompts that I use" (current message)


  averigua todo lo que necites   
  para hacer la integracion del   
  API de ratings en el frontend,  
  busca los archivos dentro del   
  backend que tengan relevancia   
  para tu integracion

  utilizando el contexto has la     integracion del API para que      traiga el rating del curso (en    la pagina de lista de cursos)     para mostrar el valor que viene    del API ya que usamos un         mocked


  check tokens  npx ccusage@latest daily --since 20260210 --until 20260505