terraform {
  required_providers {
    vsphere = {
      source  = "hashicorp/vsphere"
      version = "~> 2.5"
    }
  }
}

provider "vsphere" {
  user           = var.vsphere_user
  password       = var.vsphere_password
  vsphere_server = var.vsphere_server
  allow_unverified_ssl = var.vsphere_allow_unverified_ssl
}

data "vsphere_datacenter" "dc" {
  name = var.datacenter_name
}

data "vsphere_datastore" "datastore" {
  name          = var.datastore_name
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_compute_cluster" "cluster" {
  name          = var.cluster_name
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = var.network_name
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_virtual_machine" "template" {
  name          = var.template_name
  datacenter_id = data.vsphere_datacenter.dc.id
}

resource "vsphere_virtual_machine" "zmovie" {
  name             = "zmovie-ubuntu26"
  resource_pool_id = data.vsphere_compute_cluster.cluster.resource_pool_id
  datastore_id     = data.vsphere_datastore.datastore.id
  num_cpus         = 4
  memory           = 24576
  guest_id         = "ubuntu64Guest"
  firmware         = "bios"
  enable_disk_uuid = true

  network_interface {
    network_id   = data.vsphere_network.network.id
    adapter_type = "vmxnet3"
  }

  disk {
    label             = "zmovie-root"
    size              = 64
    unit_number        = 0
    thin_provisioned   = true
    eagerly_scrub      = false
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template.id
  }

  extra_config = {
    "cpu_reservation"       = "1200"
    "cpu_limit"            = "2400"
    "mem_reservation"      = "16384"
    "vhv.enable"           = "TRUE"
    "hypervisor.cpuid.v0"  = "FALSE"
    "sched.cpu.max"        = "4"
    "sched.mem.max"        = "24576"
    "svga.vramSize"        = "16777216"
    "tools.syncTime"       = "TRUE"
  }

  tags = [
    var.tag_zone,
    var.tag_role,
  ]
}
