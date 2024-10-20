# Build stage
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build

# Set the working directory
WORKDIR /app

# Copy the project files
COPY ./BlazorApp/*.csproj ./
RUN dotnet restore

# Copy the entire project and build it
COPY ./BlazorApp/ ./
RUN dotnet publish -c Release -o /app/publish

# Serve stage
FROM nginx:alpine AS serve

# Copy the built Blazor WebAssembly app into the Nginx public folder
COPY --from=build /app/publish/wwwroot /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx to serve the app
CMD ["nginx", "-g", "daemon off;"]
