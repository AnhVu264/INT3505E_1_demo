/* eslint-disable no-unused-vars */
const Service = require('./Service');

/**
* Tạo sản phẩm mới
*
* productInput ProductInput 
* returns Product
* */
const createProduct = ({ productInput }) => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
        productInput,
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);
/**
* Xóa sản phẩm
*
* id String 
* no response value expected for this operation
* */
const deleteProduct = ({ id }) => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
        id,
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);
/**
* Lấy 1 sản phẩm theo ID
*
* id String 
* returns Product
* */
const getProductById = ({ id }) => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
        id,
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);
/**
* Lấy danh sách sản phẩm
*
* returns List
* */
const getProducts = () => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);
/**
* Cập nhật sản phẩm
*
* id String 
* productInput ProductInput 
* returns Product
* */
const updateProduct = ({ id, productInput }) => new Promise(
  async (resolve, reject) => {
    try {
      resolve(Service.successResponse({
        id,
        productInput,
      }));
    } catch (e) {
      reject(Service.rejectResponse(
        e.message || 'Invalid input',
        e.status || 405,
      ));
    }
  },
);

module.exports = {
  createProduct,
  deleteProduct,
  getProductById,
  getProducts,
  updateProduct,
};
