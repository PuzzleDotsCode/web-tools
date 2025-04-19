# 🛡️ De Web Pentesting Clásico a API Security Moderna

## 🧠 Giro conceptual clave

> **Antes**: el pentesting web era “pentesting de una web”.  
> **Hoy**: el pentesting web es *pentesting de una API consumida por una web (SPA)*.

---

## 📦 ¿Qué cambió?

| Ayer (PHP, JSP, etc.)            | Hoy (SPA + API + Cloud)                          |
|----------------------------------|--------------------------------------------------|
| El servidor renderiza HTML       | El navegador renderiza todo vía JavaScript      |
| Input del usuario = formulario   | Input = `fetch`, `axios`, `mutation`            |
| Lógica de negocio en PHP         | Lógica distribuida entre JS frontend y APIs     |
| Estado en cookies y sesión       | Estado en JWT, localStorage, OAuth, headers     |
| SQL vulnerable en el backend     | Llamadas a GraphQL o REST mal filtradas         |

---

## 🎯 ¿Entonces, el pentesting web moderno = API Security?

✅ **Sí, en gran medida.**

- El HTML ya no contiene la lógica del sistema.
- La interfaz visible no refleja el poder real del sistema.
- La lógica se orquesta a través de APIs, y ahí es donde ocurre la autenticación, autorización y exposición de datos.

---

## 🧰 Skillset que debes incorporar

| Disciplina moderna             | Por qué es clave |
|-------------------------------|------------------|
| API Recon                     | Para descubrir y mapear el backend real. |
| API Authentication testing    | Para explotar autenticaciones mal configuradas. |
| GraphQL exploitation          | Porque muchas apps modernas lo usan y es introspectivo. |
| JWT & token analysis          | Para detectar debilidades en sesiones y firmas. |
| Storage inspection (Web)      | Porque el estado vive en local/sessionStorage. |
| CORS, SameSite, CSP           | Para entender los límites del navegador (o romperlos). |

---

## 🔁 Cómo trasladar tus técnicas “clásicas”

| Antes                         | Hoy                                  | Acción ofensiva equivalente                      |
|------------------------------|--------------------------------------|--------------------------------------------------|
| Ver formularios HTML         | Observar `fetch`, `axios`            | Revisar DevTools → Network → Request Payload    |
| Manipular cookies            | Inspeccionar tokens y headers        | Explorar localStorage y `Authorization:`        |
| Interactuar con `login.php`  | Atacar `POST /api/auth`              | Bruteforce, token hijacking, bypass             |
| Input desde HTML             | Input desde JSON                     | Fuzzing sobre payloads estructurados            |
| SQL injection clásica        | GraphQL injection / query abuse      | Introspección, abuso de resolvers               |

---

## 🧠 Conclusión

> ✅ **Sí. Web pentesting moderno = API Security + frontend analysis.**  
> Y quien se quede pensando como en 2010, se pierde el 80% del sistema actual.

Tu conocimiento anterior **sigue siendo útil**, pero ahora necesita un nuevo escenario.  
El reto es aprender a **leer una aplicación desde la interfaz API**, no desde el DOM o HTML.

---

