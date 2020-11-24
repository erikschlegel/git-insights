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

variable "project_name" {
  type        = string
  description = "SCM project name."
}

variable "org_name" {
  type        = string
  description = "SCM organization name."
}

variable "repo_names" {
  type        = list(string)
  description = "SCM repository names."
}

variable "backlog_team_name" {
  type        = string
  description = "ADO backlog team name."
}

variable "profile_aliases" {
  type        = map(string)
  description = "Profile alias name overlay to account for discrepencies between SCM profile alias and local git profile."
}
