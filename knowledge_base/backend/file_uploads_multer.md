# Express.js File & Media Uploads with Multer

Handling `multipart/form-data` file uploads, image validation, file size limits, and static asset serving in Express applications.

## 1. Core Dependencies & Setup

```json
{
  "dependencies": {
    "express": "^4.19.2",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1"
  }
}
```

## 2. Multer Storage Engine Configuration

Configure destination folder, file naming with unique timestamps, and mime-type filters:

```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();

// Ensure upload directory exists
const UPLOADS_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

// 1. Disk Storage Engine
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOADS_DIR);
  },
  filename: (req, file, cb) => {
    // Generate safe, unique filename: timestamp-random.ext
    const ext = path.extname(file.originalname).toLowerCase();
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, `${file.fieldname}-${uniqueSuffix}${ext}`);
  }
});

// 2. File Filter (Allow only images)
const fileFilter = (req, file, cb) => {
  const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  if (allowedMimeTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type. Only JPEG, PNG, WEBP, and GIF images are allowed.'));
  }
};

// 3. Upload Middleware Instance
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5 MB maximum file size limit
  },
  fileFilter: fileFilter
});
```

## 3. Static Asset Serving & Upload Endpoints

```javascript
// Serve uploaded files statically so the frontend can display them directly
app.use('/uploads', express.static(UPLOADS_DIR));

// POST /api/upload/single - Upload single file/avatar
app.post('/api/upload/single', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file was uploaded.' });
  }

  // Construct absolute or relative URL for frontend consumption
  const fileUrl = `${req.protocol}://${req.get('host')}/uploads/${req.file.filename}`;

  res.status(201).json({
    success: true,
    message: 'File uploaded successfully',
    file: {
      originalName: req.file.originalname,
      filename: req.file.filename,
      mimetype: req.file.mimetype,
      size: req.file.size,
      url: fileUrl
    }
  });
});

// POST /api/upload/multiple - Upload batch files (e.g. gallery/attachments)
app.post('/api/upload/multiple', upload.array('photos', 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'No files uploaded.' });
  }

  const uploadedFiles = req.files.map(file => ({
    originalName: file.originalname,
    filename: file.filename,
    size: file.size,
    url: `${req.protocol}://${req.get('host')}/uploads/${file.filename}`
  }));

  res.status(201).json({
    success: true,
    count: uploadedFiles.length,
    files: uploadedFiles
  });
});

// Multer Error Handling Middleware
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File too large. Maximum limit is 5MB.' });
    }
    return res.status(400).json({ error: `Upload error: ${err.message}` });
  } else if (err) {
    return res.status(400).json({ error: err.message });
  }
  next();
});
```
