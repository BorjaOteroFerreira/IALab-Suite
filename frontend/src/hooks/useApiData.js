import React, { useState, useEffect } from 'react';

// Este hook personalizado se encarga de cargar los datos de la API
function useApiData(url, defaultValue = []) {
  const [data, setData] = useState(defaultValue);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log(`Iniciando petición a ${url}`);
        const response = await fetch(url);
        console.log(`Respuesta recibida de ${url}:`, response);
        
        if (!response.ok) {
          throw new Error(`Error en la petición: ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`Datos recibidos de ${url}:`, result);
        setData(result);
        setError(null);
      } catch (err) {
        console.error(`Error cargando datos desde ${url}:`, err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
}

export default useApiData;
