// 1. Import Product Model
const Product = require('../models/ProductModel');

/**
 * Tạo sản phẩm mới
 *
 * body ProductInput Thông tin sản phẩm
 * returns Product
 **/
exports.createProduct = async (body) => {
  try {
    const newProduct = await Product.create(body);
    return { payload: newProduct, status: 201 };
  } catch (error) {
    console.error('Lỗi khi tạo sản phẩm:', error);
    return { payload: { message: error.message }, status: 400 };
  }
};

/**
 * Xóa sản phẩm
 *
 * id String ID của sản phẩm
 * no response value expected for this operation
 **/
exports.deleteProduct = async (id) => {
  try {
    const product = await Product.findByIdAndDelete(id);
    if (!product) {
      return { payload: { message: 'Không tìm thấy sản phẩm' }, status: 404 };
    }
    return { payload: null, status: 204 }; // 204 No Content
  } catch (error) {
    console.error('Lỗi khi xóa sản phẩm:', error);
    return { payload: { message: error.message }, status: 500 };
  }
};

/**
 * Lấy 1 sản phẩm theo ID
 *
 * id String ID của sản phẩm
 * returns Product
 **/
exports.getProductById = async (id) => {
  try {
    const product = await Product.findById(id);
    if (!product) {
      return { payload: { message: 'Không tìm thấy sản phẩm' }, status: 404 };
    }
    return { payload: product, status: 200 };
  } catch (error) {
    console.error('Lỗi khi lấy sản phẩm:', error);
    return { payload: { message: error.message }, status: 500 };
  }
};

/**
 * Lấy danh sách sản phẩm
 *
 * returns List
 **/
exports.getProducts = async () => {
  try {
    const products = await Product.find();
    return { payload: products, status: 200 };
  } catch (error) {
    console.error('Lỗi khi lấy danh sách sản phẩm:', error);
    return { payload: { message: error.message }, status: 500 };
  }
};

/**
 * Cập nhật sản phẩm
 *
 * body ProductInput 
 * id String 
 * returns Product
 **/
exports.updateProduct = async (body, id) => {
  try {
    const updatedProduct = await Product.findByIdAndUpdate(id, body, {
      new: true, // Trả về document mới sau khi update
      runValidators: true, // Chạy validation của Mongoose
    });
    if (!updatedProduct) {
      return { payload: { message: 'Không tìm thấy sản phẩm' }, status: 404 };
    }
    return { payload: updatedProduct, status: 200 };
  } catch (error) {
    console.error('Lỗi khi cập nhật sản phẩm:', error);
    return { payload: { message: error.message }, status: 400 };
  }
};