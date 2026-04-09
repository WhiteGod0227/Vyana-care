import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
        primary: { main: "#2dd4bf" },
        secondary: { main: "#f97316" },
        background: { default: "#0a0f1e", paper: "#111827" },
        error: { main: "#fb7185" },
        warning: { main: "#f97316" },
        success: { main: "#2dd4bf" }
    },
    shape: { borderRadius: 16 },
    typography: {
        fontFamily: "'Outfit', 'Segoe UI', sans-serif"
    },
    components: {
        MuiButton: {
            defaultProps: { disableElevation: true },
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    textTransform: "none",
                    fontWeight: 600
                },
                contained: {
                    background: "linear-gradient(135deg, #f97316, #fb7185)",
                    "&:hover": {
                        background: "linear-gradient(135deg, #fb7185, #f97316)"
                    }
                }
            }
        },
        MuiTextField: {
            defaultProps: { size: "small" },
            styleOverrides: {
                root: {
                    "& .MuiOutlinedInput-root": {
                        color: "#e2e8f0",
                        backgroundColor: "rgba(17, 24, 39, 0.88)",
                        "& fieldset": {
                            borderColor: "#334155"
                        },
                        "&:hover fieldset": {
                            borderColor: "#475569"
                        },
                        "&.Mui-focused fieldset": {
                            borderColor: "#2dd4bf"
                        }
                    },
                    "& .MuiOutlinedInput-input::placeholder": {
                        color: "#94a3b8",
                        opacity: 1
                    }
                }
            }
        }
    }
});

export default theme;