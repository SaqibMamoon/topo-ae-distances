"""Submodules used by models."""
import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Normal
import torch.nn.functional as F
import geotorch
from .base import AutoencoderModel
# Hush the linter: Warning W0221 corresponds to a mismatch between parent class
# method signature and the child class
# pylint: disable=W0221


class ConvolutionalAutoencoder(AutoencoderModel):
    """Convolutional Autoencoder for MNIST/Fashion MNIST."""

    def __init__(self):
        """Convolutional Autoencoder."""
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=3, padding=1),  # b, 16, 10, 10
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=2),  # b, 16, 5, 5
            nn.Conv2d(16, 8, 3, stride=2, padding=1),  # b, 8, 3, 3
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=1)  # b, 8, 2, 2
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(8, 16, 3, stride=2),  # b, 16, 5, 5
            nn.ReLU(True),
            nn.ConvTranspose2d(16, 8, 5, stride=3, padding=1),  # b, 8, 15, 15
            nn.ReLU(True),
            nn.ConvTranspose2d(8, 1, 2, stride=2, padding=1),  # b, 1, 28, 28
            nn.Tanh()
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}


class View(nn.Module):
    def __init__(self, shape):
        super().__init__()
        self.shape = shape

    def forward(self, x):
        return x.view(*self.shape)

class Print(nn.Module):
    def __init__(self, name):
        self.name = name
        super().__init__()

    def forward(self, x):
        print(self.name, x.size())
        return x


class ConvolutionalAutoencoder_2D(AutoencoderModel):
    """Convolutional Autoencoder with 2d latent space.

    Architecture from:
        Model 1 in 
        `A Deep Convolutional Auto-Encoder with Pooling - Unpooling Layers in
        Caffe - Volodymyr Turchenko, Eric Chalmers, Artur Luczak`
    """
    def __init__(self, input_channels=1):
        """Convolutional Autoencoder."""
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(input_channels, 8, 9, stride=1, padding=0),  # b, 16, 10, 10
            nn.ReLU(),
            nn.Conv2d(8, 4, 9, stride=1, padding=0),  # b, 2, 3, 3
            nn.ReLU(),
            View((-1, 576)),
            nn.Linear(576, 250),
            nn.ReLU(),
            nn.Linear(250, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 250),
            nn.ReLU(),
            View((-1, 250, 1, 1)),
            nn.ReLU(),
            nn.ConvTranspose2d(250, 4, 12, stride=1, padding=0),
            nn.ReLU(),
            nn.ConvTranspose2d(4, 4, 17, stride=1, padding=0),
            nn.ReLU(),
            nn.Conv2d(4, 1, 1, stride=1, padding=0),
            nn.Tanh()
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}


class DeepAE(AutoencoderModel):
    """1000-500-250-2-250-500-1000."""
    def __init__(self, input_dims=(1, 28, 28)):
        super().__init__()
        self.input_dims = input_dims
        n_input_dims = np.prod(input_dims)
        self.encoder = nn.Sequential(
            View((-1, n_input_dims)),
            nn.Linear(n_input_dims, 1000),
            nn.ReLU(True),
            nn.BatchNorm1d(1000),
            nn.Linear(1000, 500),
            nn.ReLU(True),
            nn.BatchNorm1d(500),
            nn.Linear(500, 250),
            nn.ReLU(True),
            nn.BatchNorm1d(250),
            nn.Linear(250, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 250),
            nn.ReLU(True),
            nn.BatchNorm1d(250),
            nn.Linear(250, 500),
            nn.ReLU(True),
            nn.BatchNorm1d(500),
            nn.Linear(500, 1000),
            nn.ReLU(True),
            nn.BatchNorm1d(1000),
            nn.Linear(1000, n_input_dims),
            View((-1,) + tuple(input_dims)),
            nn.Tanh()
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}

class LinearAE(AutoencoderModel):
    """input dim - 2 - input dim."""
    def __init__(self, input_dims=(1, 28, 28)):
        super().__init__()
        self.input_dims = input_dims
        n_input_dims = np.prod(input_dims)
        self.encoder = nn.Sequential(
            View((-1, n_input_dims)),
            nn.Linear(n_input_dims, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, n_input_dims),
            View((-1,) + tuple(input_dims)),
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}

class LinearAEOrtho(AutoencoderModel):
    """input dim - 2 - input dim."""
    def __init__(self, input_dims=(1, 28, 28)):
        super().__init__()
        self.input_dims = input_dims
        n_input_dims = np.prod(input_dims)

        #Define linear encoding layer with orthogonal constraint:
        linear = nn.Linear(n_input_dims, 2)
        geotorch.orthogonal( linear, "weight")

        self.encoder = nn.Sequential(
            View((-1, n_input_dims)),
            linear, 
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, n_input_dims),
            View((-1,) + tuple(input_dims)),
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}



class RandomProjectionModel(nn.Module):
    """Conv architecture (initially for CIFAR)."""
    def __init__(self, input_dim=[3,32,32]):
        super().__init__()
        # Input size: [batch, 3, 32, 32]
        # Output size: [batch, 3, 32, 32]
        self.projection = nn.Sequential(
            nn.Conv2d(input_dim[0], 12, 4, stride=2, padding=1),            # [batch, 12, 16, 16]
            nn.ReLU(),
            nn.Conv2d(12, 24, 4, stride=2, padding=1),           # [batch, 24, 8, 8]
            nn.ReLU(),
            nn.Conv2d(24, 48, 4, stride=2, padding=1),           # [batch, 48, 4, 4] ~768 dim
            nn.ReLU(),
            )
    def forward(self, x):
        """Compute latent representation using convolutional net."""
        batch_dim = x.shape[0]
        x = self.projection(x)
        return x.view(batch_dim, -1)

class OrthoProjectionModel(nn.Module):
    """Linear, orthogonal architecture."""
    def __init__(self, input_dims=(101), n_projections=30, out_dim=20):
        super().__init__()
        n_input_dims = np.prod(input_dims)
        #linear = nn.Linear(n_input_dims, out_dim)
        self.n_projections = n_projections
        for i in range(n_projections):
            setattr(self, "fc%d" % i, nn.Linear(n_input_dims, out_dim)) 
            geotorch.orthogonal( 
                getattr(self, "fc%d" % i), 
                "weight"
            )
        self.flatten = View((-1, n_input_dims))
        #self.projection = nn.Sequential(
        #    View((-1, n_input_dims)),
        #    linear 
        #    )

    def forward(self, x):
        """Compute orthogonal linear projection"""
        outputs = []
        x = self.flatten(x)
        for i in range(self.n_projections):
            output = getattr(self, "fc%d" % i)(x)
            outputs.append(output)
        return outputs 

class MLPAutoencoder(AutoencoderModel):
    def __init__(self, arch=[3, 32, 32, 2]):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(3, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 2),
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 3)
        )
        self.reconst_error = nn.MSELoss()

    @staticmethod
    def _build_layers(arch, final_bias, final_relu):
        layers = []
        for i, (d_in, d_out) in enumerate(zip(arch, arch[1:])):
            layers.append(nn.Linear(d_in, d_out))
            if i == len(arch)-2 and not final_relu:
                layers.append(nn.ReLU(True))
        return layers

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}



class MLPAutoencoder_Spheres(AutoencoderModel):
    def __init__(self, input_dim=101, arch=[3, 32, 32, 2]):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(True),
            nn.Linear(32, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(True),
            nn.Linear(32, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(True),
            nn.Linear(32, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(True),
            nn.Linear(32, input_dim)
        )
        self.reconst_error = nn.MSELoss()

    @staticmethod
    def _build_layers(arch, final_bias, final_relu):
        layers = []
        for i, (d_in, d_out) in enumerate(zip(arch, arch[1:])):
            layers.append(nn.Linear(d_in, d_out))
            if i == len(arch)-2 and not final_relu:
                layers.append(nn.ReLU(True))
        return layers

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}


class LinearAE_Spheres(AutoencoderModel):
    def __init__(self, input_dim=101):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, input_dim)
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}

class LinearAEOrtho_Spheres(AutoencoderModel):
    def __init__(self, input_dim=101):
        super().__init__()
        
        self.encoder = nn.Linear(input_dim, 2)
        geotorch.orthogonal(self.encoder, "weight")
 
        self.decoder = nn.Sequential(
            nn.Linear(2, input_dim)
        )
        self.reconst_error = nn.MSELoss()

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        return self.encoder(x)

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        return self.decoder(z)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent = self.encode(x)
        x_reconst = self.decode(latent)
        reconst_error = self.reconst_error(x, x_reconst)
        return reconst_error, {'reconstruction_error': reconst_error}





class MLPVAE(AutoencoderModel):
    def __init__(self, input_dim=3, latent_dim=2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, latent_dim*2),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, 32),
            nn.ReLU(True),
            nn.BatchNorm1d(32),
            nn.Linear(32, input_dim*2)
        )
        self.reconst_error = nn.MSELoss()

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def _split_to_parameters(self, x):
        return x.split(x.size(-1) // 2, dim=-1)

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        mu, logvar = self._split_to_parameters(self.encoder(x))
        encoded = self.reparameterize(mu, logvar)
        return encoded

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        mu, logvar = self._split_to_parameters(self.decoder(z))
        encoded = self.reparameterize(mu, logvar)
        return encoded

    def log_likelihood(self, x, reconst_mean, reconst_std):
        predicted_x = Normal(loc=reconst_mean, scale=reconst_std)
        return predicted_x.log_prob(x).sum(dim=-1)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        latent_mu, latent_logvar = self._split_to_parameters(self.encoder(x))
        latent = self.reparameterize(latent_mu, latent_logvar)

        data_mu, data_logvar = self._split_to_parameters(self.decoder(latent))
        data_std = torch.exp(0.5*data_logvar)

        likelihood = -self.log_likelihood(x, data_mu, data_std).mean(dim=0)

        # 0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
        kl_div = -0.5 * torch.sum(
            1 + latent_logvar - latent_mu.pow(2) - latent_logvar.exp(),
            dim=-1
        ).mean(dim=0)
        loss = likelihood + kl_div
        reconst_error = self.reconst_error(x, data_mu)
        return loss, {'loss.likelihood': likelihood, 'loss.kl_divergence': kl_div, 'reconstruction_error': reconst_error}


class DeepVAE(AutoencoderModel):
    """1000-500-250-(2+2)-250-500-1000. 
     DeepAE architecture, but with VAE (therefore 4 latent dims for each 2 means, vars)
    """
    def __init__(self, input_dims=(1, 28, 28), latent_dim=2):
        super().__init__()
        self.input_dims = input_dims
        n_input_dims = np.prod(input_dims)
        self.encoder = nn.Sequential(
            View((-1, n_input_dims)),
            nn.Linear(n_input_dims, 1000),
            nn.ReLU(True),
            #nn.BatchNorm1d(1000),
            nn.Linear(1000, 500),
            nn.ReLU(True),
            #nn.BatchNorm1d(500),
            nn.Linear(500, 250),
            nn.ReLU(True),
            #nn.BatchNorm1d(250),
            nn.Linear(250, latent_dim*2),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 250),
            nn.ReLU(True),
            #nn.BatchNorm1d(250),
            nn.Linear(250, 500),
            nn.ReLU(True),
            #nn.BatchNorm1d(500),
            nn.Linear(500, 1000),
            nn.ReLU(True),
            #nn.BatchNorm1d(1000),
            nn.Linear(1000, n_input_dims),
            View((-1,) + tuple(input_dims) ),
            nn.Sigmoid(), #nn.Tanh(), 
        )
        self.reconst_error = nn.MSELoss()
        #self.criterion = nn.BCELoss() 
 
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def _split_to_parameters(self, x):
        mu, logvar = x.split(x.size(-1) // 2, dim=-1)
        if mu.size()[-1] == 1: #there is one superfluous dim, squeeze it away
            mu, logvar = mu.squeeze(dim=-1), logvar.squeeze(dim=-1)  
        return mu, logvar
        #return x.split(x.size(-1) // 2, dim=-1)

    def encode(self, x):
        """Compute latent representation using convolutional autoencoder."""
        mu, logvar = self._split_to_parameters(self.encoder(x))
        encoded = self.reparameterize(mu, logvar)
        return encoded

    def decode(self, z):
        """Compute reconstruction using convolutional autoencoder."""
        #mu, logvar = self._split_to_parameters(self.decoder(z))
        #encoded = self.reparameterize(mu, logvar)
        #return encoded
        decoded = self.decoder(z)
        return (decoded - 0.5)*2 
    
    def log_likelihood(self, x, reconst_mean, reconst_std):
        predicted_x = Normal(loc=reconst_mean, scale=reconst_std)
        return predicted_x.log_prob(x).sum(dim=-1)

    def forward(self, x):
        """Apply autoencoder to batch of input images.

        Args:
            x: Batch of images with shape [bs x channels x n_row x n_col]

        Returns:
            tuple(reconstruction_error, dict(other errors))

        """
        batch_size = x.size()[0]
        #input_dims = np.prod(x.size()[1:])
        latent_mu, latent_logvar = self._split_to_parameters(self.encoder(x))
        latent = self.reparameterize(latent_mu, latent_logvar)
    
        reconstruction = self.decoder(latent)
        #data_mu, data_logvar = self._split_to_parameters(self.decoder(latent))
        #data_std = torch.exp(0.5*data_logvar)
        
        #likelihood = -self.log_likelihood(x.view(batch_size, -1), data_mu.view(batch_size, -1), data_std.view(batch_size, -1) ).mean()
        #likelihood = -self.log_likelihood(x.view(batch_size, -1), data_mu.view(batch_size, -1), data_std.view(batch_size, -1) ).mean(dim=0)
        #device=torch.device('cuda')
        x_rescaled = (x/2) + 0.5 #.to(device=device)
        #print(f'x_rescaled min: {x_rescaled.min().cpu()}')        
        #print(f'x_rescaled max: {x_rescaled.max().cpu()}')
        #print(f'reconstruction min: {reconstruction.min().cpu()}') 
        #print(f'reconstruction max: {reconstruction.max().cpu()}') 
        
        #likelihood = self.criterion(reconstruction.to('cuda'), x_rescaled.to('cuda'))
        likelihood = F.binary_cross_entropy(reconstruction, x_rescaled, reduction='sum') # 'sum' #this version worked best
        #likelihood = F.binary_cross_entropy_with_logits(reconstruction, x)
        
        kl_div = -0.5 * torch.sum(1 + latent_logvar - latent_mu.pow(2) - latent_logvar.exp())
        #kl_div = -0.5 * torch.sum(
        #    1 + latent_logvar.view(batch_size, -1) - latent_mu.view(batch_size, -1).pow(2) - latent_logvar.view(batch_size, -1).exp(),
        #    dim=-1
        #).mean() #(dim=0)
        
        loss = likelihood + kl_div
        reconst_error = self.reconst_error(x, (reconstruction - 0.5)*2  )
        return loss, {'loss.likelihood': likelihood, 'loss.kl_divergence': kl_div, 'reconstruction_error': reconst_error}
