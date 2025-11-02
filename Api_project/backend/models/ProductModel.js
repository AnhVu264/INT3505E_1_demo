const mongoose = require('mongoose');

const productSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Tên sản phẩm là bắt buộc'],
      trim: true,
    },
    price: {
      type: Number,
      required: [true, 'Giá sản phẩm là bắt buộc'],
      min: [0, 'Giá không thể âm'],
    },
    description: {
      type: String,
      trim: true,
    },
  },
  {
    timestamps: true, // Tự động thêm createdAt và updatedAt
    toJSON: {
      // Biến đổi _id thành id khi trả về JSON
      transform: (doc, ret) => {
        ret.id = ret._id;
        delete ret._id;
        delete ret.__v;
      },
    },
  }
);

const Product = mongoose.model('Product', productSchema);
module.exports = Product;