# Build stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

# Set the working directory
WORKDIR /app

# Copy the project files
COPY ./BlazorApp/*.csproj ./ 
RUN dotnet restore

# Copy the entire project
COPY ./BlazorApp/ ./

# Expose port 80 (o cualquier otro puerto que prefieras)
EXPOSE 80

# Run the Blazor app
CMD ["dotnet", "run", "--urls", "http://0.0.0.0:80"]
