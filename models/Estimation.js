// models/Estimation.js
const mongoose = require('mongoose');

const estimationItemSchema = new mongoose.Schema({
  material: { type: mongoose.Schema.Types.ObjectId, ref: 'Material' },
  quantity: { type: Number, required: true },
  unitPrice: { type: Number, required: true },
  description: String
});

const estimationSchema = new mongoose.Schema({
  projectName: { type: String, required: true },
  items: [estimationItemSchema],
  createdAt: { type: Date, default: Date.now },
  totalCost: { type: Number },
  createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
});

module.exports = mongoose.model('Estimation', estimationSchema);
