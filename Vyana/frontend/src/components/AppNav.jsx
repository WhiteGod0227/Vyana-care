import { Link, useLocation } from "react-router-dom";
import { Box, Button, Paper, Stack, Typography } from "@mui/material";

const links = [
  { to: "/", label: "मरीज पोर्टल" },
  { to: "/asha", label: "आशा डैशबोर्ड" },
  { to: "/district", label: "जिला डैशबोर्ड" },
];

function AppNav({ title, subtitle }) {
  const location = useLocation();

  return (
    <Paper sx={{ p: 2, mb: 2 }} elevation={1}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
        <Box>
          <Typography variant="h5" fontWeight={700} color="primary.main">
            {title}
          </Typography>
          {subtitle ? (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          ) : null}
        </Box>
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {links.map((item) => (
            <Button
              key={item.to}
              component={Link}
              to={item.to}
              variant={location.pathname === item.to ? "contained" : "outlined"}
              size="small"
              sx={{ mt: { xs: 1, md: 0 } }}
            >
              {item.label}
            </Button>
          ))}
        </Stack>
      </Stack>
    </Paper>
  );
}

export default AppNav;
