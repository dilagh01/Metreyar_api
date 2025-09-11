// models/Material.js
const mongoose = require('mongoose');

const materialSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  unit: { type: String, required: true }, // متر، کیلوگرم، عدد
  category: { type: String, required: true },
  unitPrice: { type: Number, required: true },
  description: String,
  lastUpdated: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Material', materialSchema);
