const jwt = require('jsonwebtoken');
const User = require('../models/UserModel');

exports.protect = async (req, res, next) => {
  let token;
  // Kiểm tra xem header Authorization có Bearer token không
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      // Lấy token từ header
      token = req.headers.authorization.split(' ')[1];
      // Xác thực token
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      // Lấy thông tin user (trừ mật khẩu) và gắn vào request
      req.user = await User.findById(decoded.id).select('-password');
      next(); // Đi tiếp
    } catch (error) {
      console.error(error);
      res.status(401).json({ message: 'Không được phép, token thất bại' });
    }
  }
  if (!token) {
    res.status(401).json({ message: 'Không được phép, không có token' });
  }
};