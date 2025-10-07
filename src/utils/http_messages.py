HTTP_OK_MESSAGE = 'Success.'
HTTP_CREATED_MESSAGE = 'Created.'
HTTP_BAD_REQUEST_MESSAGE = 'Bad Request.'
HTTP_UNAUTHORIZED_MESSAGE = 'Unauthorized.'
HTTP_NOT_FOUND_MESSAGE = 'Not Found.'
HTTP_CONFLICT_MESSAGE = 'Conflict.'
HTTP_INTERNAL_SERVER_ERROR_MESSAGE = 'Internal Server Error.'

HTTP_TOKEN_REQUIRED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + ' ' + 'Token is required.'
HTTP_TOKEN_EXPIRED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + ' ' + 'Token expired!'
HTTP_INVALID_SIGNATURE_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + ' ' + 'Invalid signature!'
HTTP_INVALID_TOKEN_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + ' ' + 'Invalid token!'

HTTP_REGISTER_BAD_REQUEST_MESSAGE = HTTP_BAD_REQUEST_MESSAGE + \
    ' ' + 'All fields (email, username, password, user_type) are required.'
HTTP_REGISTER_USER_EXISTS_MESSAGE = HTTP_CONFLICT_MESSAGE + \
    ' ' + 'User already exists.'
HTTP_REGISTER_CREATED_MESSAGE = HTTP_CREATED_MESSAGE + \
    ' ' + 'User created successfully.'

HTTP_LOGIN_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + ' ' + 'Login successful!'
HTTP_LOGIN_BAD_REQUEST_MESSAGE = HTTP_BAD_REQUEST_MESSAGE + \
    ' ' + 'All fields (email, password) are required.'
HTTP_LOGIN_INVALID_CREDENTIALS_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Invalid credentials.'

HTTP_GET_USER_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + \
    ' ' + 'User details retrieved successfully!'
HTTP_GET_USER_BY_EMAIL_UNAUTHORIZED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Unauthorized to view other user details.'
HTTP_GET_USER_BY_ID_UNAUTHORIZED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Unauthorized to view other user details using Id.'

HTTP_USER_NOT_FOUND_MESSAGE = HTTP_NOT_FOUND_MESSAGE + ' ' + 'User not found.'

HTTP_PASSWORD_UPDATE_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + \
    ' ' + 'Password updated successfully!'
HTTP_PASSWORD_UPDATE_BAD_REQUEST_MESSAGE = HTTP_BAD_REQUEST_MESSAGE + \
    ' ' + 'Passwords do not match!'

HTTP_DELETE_USER_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + \
    ' ' + 'User deleted successfully!'
HTTP_DELETE_USER_UNAUTHORIZED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Unauthorized to delete user.'
HTTP_DELETE_USER_SUPER_ADMIN_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Unauthorized to delete the super admin user.'
HTTP_DELETE_USER_SELF_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Unauthorized to delete your own admin account.'

HTTP_GET_PATIENTS_UNAUTHORIZED_MESSAGE = HTTP_UNAUTHORIZED_MESSAGE + \
    ' ' + 'Only admin can access all patients.'
HTTP_GET_PATIENTS_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + \
    ' ' + 'Patients retrieved successfully!'

HTTP_GET_DOCTORS_SUCCESS_MESSAGE = HTTP_OK_MESSAGE + \
    ' ' + 'Doctors retrieved successfully!'