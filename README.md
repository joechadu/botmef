# 🤖 MEF Bot — Consulta de Expedientes y Certificados

Bot de Telegram para consultar **expedientes** y **certificados** del [Ministerio de Economía y Finanzas del Perú (MEF)](https://www.mef.gob.pe/) directamente desde tu celular o escritorio, sin necesidad de navegar la web.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Comandos Disponibles](#-comandos-disponibles)
- [Flujo de Conversación](#-flujo-de-conversación)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Solución de Problemas](#-solución-de-problemas)
- [Licencia](#-licencia)

---

## 📖 Descripción

**MEF Bot** automatiza las consultas al portal web del MEF (`apps2.mef.gob.pe`), permitiendo a los usuarios obtener información de expedientes SIAF y certificados de crédito presupuestario a través de una interfaz conversacional en Telegram.

El bot maneja todo el proceso: desde la captura de parámetros de búsqueda hasta la resolución del captcha, entregando los resultados como un resumen en chat y un archivo Excel descargable.

---

## ✨ Características

| Funcionalidad | Detalle |
|---|---|
| **Consulta de expedientes** | Búsqueda por año, unidad ejecutora y número de expediente SIAF |
| **Consulta de certificados** | Búsqueda por año, unidad ejecutora y número de certificado |
| **Resolución de captcha** | Envía la imagen captcha al usuario para ingreso manual |
| **Exportación a Excel** | Genera archivos `.xlsx` con los resultados tabulados |
| **Reintento de captcha** | Permite reintentar si el captcha fue ingresado incorrectamente |
| **Gestión de sesiones** | Manejo seguro de sesiones HTTP con cierre automático para evitar fugas de memoria |
| **Validación de datos** | Validación de año, código de unidad ejecutora y número de documento |
| **Flujo conversacional** | Interfaz guiada paso a paso con teclados interactivos |

---

## 🏗 Arquitectura

```
Usuario (Telegram)
    │
    ▼
┌──────────────────┐
│   Telegram Bot    │  python-telegram-bot v22.5
│   (main.py)       │  ConversationHandler
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  aiohttp Session  │  Sesión HTTP persistente con cookies
│  (async client)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  MEF Web Portal   │  apps2.mef.gob.pe
│  (GET + POST)     │  HTML parsing con BeautifulSoup
└──────────────────┘
```

El bot opera de forma **completamente asíncrona**, utilizando `aiohttp` para las peticiones HTTP y la API async de `python-telegram-bot` para la interacción con los usuarios.

---

## 📦 Requisitos Previos

- **Python** 3.10 o superior
- **pip** (gestor de paquetes de Python)
- Un **Bot de Telegram** registrado vía [@BotFather](https://t.me/BotFather)
- Conexión a internet para acceder al portal del MEF

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/joechadu/botmef.git
cd botmef
```

### 2. Crear y activar el entorno virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuración

### Token del Bot

Antes de ejecutar, debes configurar tu token de Telegram. En `main.py`, reemplaza el token en la función `main()`:

```python
application = ApplicationBuilder().token("TU_TOKEN_AQUI").build()
```

> **⚠️ Importante:** Nunca subas tu token real a un repositorio público. Considera usar variables de entorno:
>
> ```python
> import os
> token = os.getenv("MEF_BOT_TOKEN")
> application = ApplicationBuilder().token(token).build()
> ```

---

## 💬 Uso

### Ejecutar el bot

```bash
python main.py
```

Verás en consola:

```
🤖 Iniciando bot del MEF...
✅ Bot iniciado y escuchando actualizaciones.
```

### Interactuar en Telegram

1. Abre Telegram y busca tu bot por el username asignado en BotFather
2. Envía `/start` para ver el menú principal
3. Selecciona el tipo de consulta
4. Sigue las indicaciones paso a paso

---

## 📌 Comandos Disponibles

| Comando | Descripción |
|---|---|
| `/start` | Inicia el bot y muestra el menú principal |
| `/consulta_exp` | Inicia una consulta de **expediente SIAF** |
| `/consulta_cert` | Inicia una consulta de **certificado de crédito presupuestario** |
| `/cancelar` | Cancela la consulta en curso y regresa al menú |

---

## 🔄 Flujo de Conversación

```mermaid
flowchart TD
    A[/start] --> B{Seleccionar consulta}
    B -->|/consulta_exp| C[Ingresar año]
    B -->|/consulta_cert| C
    C --> D[Ingresar unidad ejecutora]
    D --> E[Ingresar número]
    E --> F[Bot envía captcha 🖼️]
    F --> G[Ingresar captcha]
    G --> H{¿Captcha correcto?}
    H -->|Sí| I[✅ Muestra resultados + Excel]
    H -->|No| F
    I --> J{¿Otra consulta?}
    J -->|Sí| B
    J -->|No| K[👋 Fin]
```

### Detalle de cada paso

| Paso | Estado | Validación |
|---|---|---|
| 1. Año de ejecución | `PEDIR_ANIO` | Numérico, rango 2020 – año actual |
| 2. Unidad ejecutora | `PEDIR_UNIDAD` | Numérico, máximo 6 dígitos |
| 3. Número de documento | `PEDIR_NUM` | Numérico, máximo 10 dígitos |
| 4. Captcha | `PEDIR_CAPTCHA` | Texto libre, validado por el servidor MEF |
| 5. ¿Otra consulta? | `CONSULTA_FINAL` | Solo acepta "Sí" o "No" |

---

## 🛠 Stack Tecnológico

| Tecnología | Versión | Propósito |
|---|---|---|
| [Python](https://python.org) | 3.10+ | Lenguaje base |
| [python-telegram-bot](https://python-telegram-bot.org/) | 22.5 | Interacción con la API de Telegram |
| [aiohttp](https://docs.aiohttp.org/) | 3.13.0 | Cliente HTTP asíncrono (sesiones con cookies) |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | 4.14.2 | Parsing de HTML del portal MEF |
| [pandas](https://pandas.pydata.org/) | 2.3.3 | Manipulación de datos tabulares |
| [openpyxl](https://openpyxl.readthedocs.io/) | 3.1.5 | Generación de archivos Excel `.xlsx` |

---

## 📂 Estructura del Proyecto

```
mef_bot/
├── main.py              # Lógica principal del bot
├── requirements.txt     # Dependencias del proyecto
├── captcha.jpg          # Archivo temporal de captcha (generado en runtime)
├── .gitignore           # Archivos excluidos del repositorio
└── README.md            # Este archivo
```

---

## 🔧 Solución de Problemas

| Problema | Causa posible | Solución |
|---|---|---|
| `UnicodeEncodeError` con emojis | Consola Windows sin UTF-8 | El bot ya incluye `sys.stdout.reconfigure(encoding="utf-8")` |
| "No se pudo obtener captcha" | Portal MEF caído o cambio en el HTML | Verificar que `apps2.mef.gob.pe` esté activo |
| Captcha siempre incorrecto | Cookies no se mantienen entre peticiones | Verificar que `aiohttp.ClientSession` se reutiliza correctamente |
| Bot no responde | Token inválido o proceso detenido | Verificar token y que `main.py` esté en ejecución |
| `ModuleNotFoundError` | Entorno virtual no activado | Activar `.venv` antes de ejecutar |

---

## 📄 Licencia

Este proyecto es de uso interno / educativo.

---

<p align="center">Desarrollado con ❤️ por</p>

```diff
+    ****    *****   ******  *****
+   *    *   *    *  *       *    *
+   *    *   *****   ****    *    *
+   *    *   *    *  *       *    *
+    ****    *****   ******  *****
```

