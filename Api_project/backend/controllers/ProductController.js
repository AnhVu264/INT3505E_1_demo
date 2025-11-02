const service = require('../services/ProductService');

// Hàm trợ giúp để gửi phản hồi
const handleResponse = (response, { payload, status }) => {
  response.status(status).json(payload);
};

// Hàm trợ giúp để bắt lỗi
const handleError = (response, error) => {
  console.error(error); // In lỗi ra terminal
  response.status(500).json({ message: error.message || 'Lỗi server nội bộ' });
};

const createProduct = async (request, response) => {
  try {
    // Tự tay lấy request.body và truyền vào service
    const result = await service.createProduct(request.body);
    handleResponse(response, result);
  } catch (error) {
    handleError(response, error);
  }
};

const deleteProduct = async (request, response) => {
  try {
    // Tự tay lấy request.params.id và truyền vào service
    const result = await service.deleteProduct(request.params.id);
    handleResponse(response, result);
  } catch (error) {
    handleError(response, error);
  }
};

const getProductById = async (request, response) => {
  try {
    // Tự tay lấy request.params.id
    const result = await service.getProductById(request.params.id);
    handleResponse(response, result);
  } catch (error) {
    handleError(response, error);
  }
};

const getProducts = async (request, response) => {
  try {
    // Hàm này không cần tham số
    const result = await service.getProducts();
    handleResponse(response, result);
  } catch (error) {
    handleError(response, error);
  }
};

const updateProduct = async (request, response) => {
  try {
    // Tự tay lấy cả body và id
    const result = await service.updateProduct(request.body, request.params.id);
    handleResponse(response, result);
  } catch (error) {
    handleError(response, error);
  }
};

module.exports = {
  createProduct,
  deleteProduct,
  getProductById,
  getProducts,
  updateProduct,
};