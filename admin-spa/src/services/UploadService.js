import AuthService from "./AuthService";

const UploadService = {
  async upload(file) {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await AuthService.api.post("/admin/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data.url;
  },
};

// Example usage:
// const url = await UploadService.upload(fileInput.files[0]);

export default UploadService;
