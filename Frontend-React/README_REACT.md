# Integración de React con Flask para IALab Suite

Este proyecto integra un frontend en React con el backend de Flask existente para IALab Suite.

## Estructura del proyecto

```

├── Frontend-React/        # Aplicación React
    ├── public/            # Archivos estáticos
    ├── src/               # Código fuente de React
    │   ├── components/    # Componentes React
    │   ├── context/       # Contextos para gestión de estado
    │   ├── hooks/         # Hooks personalizados
    │   ├── services/      # Servicios para API
    │   ├── App.js         # Componente principal
    │   └── index.js       # Punto de entrada
    └── package.json       # Dependencias

```

## Requisitos previos

- Node.js y npm instalados
- Python 3.x instalado
- Dependencias de Python ya instaladas

## Pasos para configurar y ejecutar

### 1. Instalar dependencias de React

```bash
cd frontend
npm install
```

### 2. Compilar la aplicación React

```bash
cd frontend
npm run build
```

### 3. Iniciar el servidor Flask que sirve React

```bash
python start_react_app.py
```

### 4. Acceder a la aplicación

Abre un navegador y ve a `http://localhost:5000`

## Desarrollo

Para desarrollo, puedes ejecutar el servidor React en modo de desarrollo:

```bash
cd frontend
npm start
```

Esto iniciará el servidor de desarrollo de React en `http://localhost:3000` que automáticamente enviará las solicitudes de API al servidor Flask en el puerto 5000 (gracias a la configuración del proxy en package.json).

## Notas importantes

- La aplicación React usa Socket.io para la comunicación en tiempo real con el backend
- Las APIs del backend Flask se mantienen igual que en la versión original
- Se ha añadido CORS para permitir que el frontend de desarrollo se comunique con el backend
