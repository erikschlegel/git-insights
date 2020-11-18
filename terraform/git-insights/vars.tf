variable "service_name" {
  type        = string
  default     = "gitinsights"
  description = "Name of service. Used as a resource prefix."
}

variable "env" {
  type        = string
  default     = "dev"
  description = "Environment (i.e., dev, int, prod)."
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "token" {
  type        = string
  description = "Token used to authenticate with git hosting service (ADO, GitHub, GitLab)."
}

variable "ado_config" {
  type = object({
    project_name      = string,
    org_name          = string,
    repo_names        = list(string),
    backlog_team_name = string,
    profile_aliases   = map(string)
  })
  description = "Azure DevOps configuration. repo_names should be comma-delimited. profile_aliases should be a map of key value pairs for alias overrides."
}
