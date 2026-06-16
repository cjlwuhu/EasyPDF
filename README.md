# EasyPDF

EasyPDF is a local-first web app for reading English academic PDFs in Chinese with a side-by-side original PDF and translated paragraph reader.

## Local Setup

1. Create the MySQL database:

   ```powershell
   Get-Content -Raw scripts\init-db.sql | mysql -uroot -p123456
   ```

2. Configure the backend:

   ```powershell
   cd backend
   Copy-Item .env.example .env
   ```

   Fill `MYSQL_PASSWORD`, `API_KEY`, `BASE_URL`, and `MODEL_NAME` in `backend\.env`.

3. Run migrations:

   ```powershell
   conda activate lang-chain01
   cd backend
   alembic upgrade head
   ```

4. Install and build the frontend:

   ```powershell
   cd ..\frontend
   npm.cmd install
   npm.cmd run build
   ```

5. Start both services:

   ```powershell
   cd ..
   .\scripts\dev.cmd
   ```

Open `http://127.0.0.1:5173`.
