import client from "./client";

export type CertificateStatus = {
  available: boolean;
  url?: string;
};

export const certificatesApi = {
  async my(): Promise<CertificateStatus> {
    const { data } = await client.get<CertificateStatus>("/certificates/my");
    return data || { available: false };
  },
};

export default certificatesApi;
