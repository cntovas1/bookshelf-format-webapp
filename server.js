// server.js
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

app.use(cors());

const app = express();
app.use(express.static('public'));

const upload = multer({ dest: 'uploads/' });

app.post('/upload', upload.array('files'), async (req, res) => {
  const formData = new FormData();
  req.files.forEach(file => {
    formData.append('files', fs.createReadStream(file.path), file.originalname);
  });

  try {
    const response = await axios.post('https://flask-backend-2pfq.onrender.com/process', formData, {
      headers: formData.getHeaders(),
      responseType: 'arraybuffer', // Image data
    });

    res.set('Content-Type', 'image/png');
    res.send(response.data);
  } catch (error) {
    console.error('Error generating visualization:', error.message);
    res.status(500).json({ message: 'Error generating visualization. Files missing.', error: error.message });
  } finally {
    req.files.forEach(file => fs.unlink(file.path, (err) => {
      if (err) console.error(`Failed to delete file ${file.path}:`, err);
    }));
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

