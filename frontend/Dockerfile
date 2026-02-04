FROM nginx:alpine
# Imagen base de Nginx en Alpine Linux (muy ligera), ideal para servir archivos estáticos (frontend)

COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copia la configuración personalizada de Nginx reemplazando el default server config
# (default.conf es el virtual host por defecto en esta imagen)

COPY public /usr/share/nginx/html
# Copia los archivos estáticos del frontend (HTML/CSS/JS) al directorio estándar que Nginx sirve por defecto

EXPOSE 80
# Documenta que el contenedor expone el puerto 80 (HTTP)
# Nota: EXPOSE no publica el puerto automáticamente; se publica al usar -p o en docker-compose
