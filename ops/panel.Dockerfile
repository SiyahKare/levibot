# ---- build panel ----
FROM node:20-alpine AS build
WORKDIR /ui
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
# output: /ui/dist

# ---- export to named volume via helper ----
FROM busybox:1.36
WORKDIR /export
COPY --from=build /ui/dist ./dist
CMD ["sh","-c","cp -r /export/dist/* /mnt/panel && ls -la /mnt/panel"]
